"""
Management command to load IANA timezone data into MySQL timezone tables.
Uses the tzdata Python package (already installed) to read TZif files.
Required because MySQL on Windows doesn't automatically have timezone tables populated.

Usage: python manage.py load_mysql_timezones
"""
import os
import struct
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection


def parse_tzif_v2(data):
    """
    Parse a TZif v2/v3 file and return (transitions, transition_types, abbrs).
    transitions: list of (unix_timestamp, type_index)
    transition_types: list of (utoff_seconds, is_dst, abbr_index)
    abbrs: bytes containing null-terminated abbreviation strings
    """
    # V2 files start with a V1 section then a V2 section (magic 'TZif' again)
    v2_start = data.find(b'TZif', 1)
    if v2_start == -1:
        # Fall back to V1 parsing (4-byte timestamps)
        return _parse_tzif_v1(data)

    # Parse V2 header (44 bytes: 4 magic + 1 version + 15 padding + 6x4 counts)
    header = struct.unpack('>6l', data[v2_start + 20: v2_start + 44])
    ttisgmtcnt, ttisstdcnt, ttleapcnt, timecnt, typecnt, charcnt = header

    offset = v2_start + 44

    # Transition times: 8-byte signed integers (V2)
    transitions_raw = struct.unpack(f'>{timecnt}q', data[offset: offset + timecnt * 8])
    offset += timecnt * 8

    # Transition type indices
    tt_indices = struct.unpack(f'>{timecnt}B', data[offset: offset + timecnt])
    offset += timecnt

    # ttinfo structs: utoff (4-byte signed), dst (1-byte), abbr_idx (1-byte)
    ttinfos = []
    for _ in range(typecnt):
        utoff, dst, abbr_idx = struct.unpack('>iBB', data[offset: offset + 6])
        ttinfos.append((utoff, dst, abbr_idx))
        offset += 6

    abbrs = data[offset: offset + charcnt]

    transitions = list(zip(transitions_raw, tt_indices))
    return transitions, ttinfos, abbrs


def _parse_tzif_v1(data):
    """Fallback V1 parser with 4-byte timestamps."""
    header = struct.unpack('>6l', data[20:44])
    ttisgmtcnt, ttisstdcnt, ttleapcnt, timecnt, typecnt, charcnt = header

    offset = 44
    transitions_raw = struct.unpack(f'>{timecnt}i', data[offset: offset + timecnt * 4])
    offset += timecnt * 4
    tt_indices = struct.unpack(f'>{timecnt}B', data[offset: offset + timecnt])
    offset += timecnt
    ttinfos = []
    for _ in range(typecnt):
        utoff, dst, abbr_idx = struct.unpack('>iBB', data[offset: offset + 6])
        ttinfos.append((utoff, dst, abbr_idx))
        offset += 6
    abbrs = data[offset: offset + charcnt]

    transitions = list(zip(transitions_raw, tt_indices))
    return transitions, ttinfos, abbrs


def get_abbr(abbrs, idx):
    """Extract null-terminated string from abbrs bytes at index idx."""
    end = abbrs.index(b'\x00', idx)
    return abbrs[idx:end].decode('ascii', errors='replace')


def find_tzif_files(zoneinfo_dir):
    """Walk the zoneinfo directory and yield (tz_name, file_path) pairs."""
    zoneinfo_path = Path(zoneinfo_dir)
    for root, dirs, files in os.walk(zoneinfo_path):
        # Skip __pycache__ and similar
        dirs[:] = [d for d in dirs if not d.startswith('_') and d != 'posix' and d != 'right']
        for fname in files:
            if fname.startswith('_') or fname.endswith('.py') or fname.endswith('.pyc'):
                continue
            fpath = Path(root) / fname
            # Check it's a TZif file
            try:
                with open(fpath, 'rb') as f:
                    magic = f.read(4)
                if magic != b'TZif':
                    continue
            except (IOError, OSError):
                continue
            # Compute timezone name relative to zoneinfo dir
            rel = fpath.relative_to(zoneinfo_path)
            tz_name = rel.as_posix()
            yield tz_name, str(fpath)


class Command(BaseCommand):
    help = 'Load IANA timezone data from tzdata package into MySQL timezone tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--truncate',
            action='store_true',
            default=True,
            help='Truncate existing timezone tables before loading (default: True)',
        )

    def handle(self, *args, **options):
        try:
            import tzdata
            zoneinfo_dir = str(Path(tzdata.__file__).parent / 'zoneinfo')
        except ImportError:
            self.stderr.write('tzdata package not found. Install with: pip install tzdata')
            return

        self.stdout.write(f'Loading timezones from: {zoneinfo_dir}')

        with connection.cursor() as cursor:
            # Verify we're on MySQL
            engine = connection.settings_dict['ENGINE']
            if 'mysql' not in engine:
                self.stderr.write(f'This command is for MySQL only. Engine: {engine}')
                return

            # Truncate existing data
            self.stdout.write('Truncating existing timezone tables...')
            cursor.execute('TRUNCATE TABLE mysql.time_zone_transition_type')
            cursor.execute('TRUNCATE TABLE mysql.time_zone_transition')
            cursor.execute('TRUNCATE TABLE mysql.time_zone_name')
            cursor.execute('TRUNCATE TABLE mysql.time_zone')

            tz_files = list(find_tzif_files(zoneinfo_dir))
            self.stdout.write(f'Found {len(tz_files)} timezone files')

            loaded = 0
            errors = 0

            for tz_name, fpath in tz_files:
                try:
                    with open(fpath, 'rb') as f:
                        data = f.read()

                    transitions, ttinfos, abbrs = parse_tzif_v2(data)

                    # Insert time_zone row
                    cursor.execute(
                        "INSERT INTO mysql.time_zone (Use_leap_seconds) VALUES ('N')"
                    )
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    tz_id = cursor.fetchone()[0]

                    # Insert time_zone_name
                    cursor.execute(
                        "INSERT INTO mysql.time_zone_name (Name, Time_zone_id) VALUES (%s, %s)",
                        [tz_name, tz_id]
                    )

                    # Insert transition types
                    for type_idx, (utoff, is_dst, abbr_idx) in enumerate(ttinfos):
                        abbr = get_abbr(abbrs, abbr_idx) if abbrs else 'UTC'
                        cursor.execute(
                            "INSERT INTO mysql.time_zone_transition_type "
                            "(Time_zone_id, Transition_type_id, Offset, Is_DST, Abbreviation) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            [tz_id, type_idx, utoff, int(is_dst), abbr[:8]]
                        )

                    # Insert transitions
                    for trans_time, type_idx in transitions:
                        cursor.execute(
                            "INSERT INTO mysql.time_zone_transition "
                            "(Time_zone_id, Transition_time, Transition_type_id) "
                            "VALUES (%s, %s, %s)",
                            [tz_id, trans_time, type_idx]
                        )

                    loaded += 1
                    if loaded % 100 == 0:
                        self.stdout.write(f'  Loaded {loaded}/{len(tz_files)}...')

                except Exception as e:
                    errors += 1
                    if options.get('verbosity', 1) >= 2:
                        self.stderr.write(f'  Error loading {tz_name}: {e}')

            # Also add UTC alias if not already present (some systems need it)
            try:
                cursor.execute("SELECT COUNT(*) FROM mysql.time_zone_name WHERE Name = 'UTC'")
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        "INSERT INTO mysql.time_zone (Use_leap_seconds) VALUES ('N')"
                    )
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    utc_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO mysql.time_zone_name (Name, Time_zone_id) VALUES ('UTC', %s)",
                        [utc_id]
                    )
                    cursor.execute(
                        "INSERT INTO mysql.time_zone_transition_type "
                        "(Time_zone_id, Transition_type_id, Offset, Is_DST, Abbreviation) "
                        "VALUES (%s, 0, 0, 0, 'UTC')",
                        [utc_id]
                    )
            except Exception:
                pass

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Loaded {loaded} timezones, {errors} errors.'
            )
        )
