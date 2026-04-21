from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    """Tests para el modelo User personalizado"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Test creación de usuario"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
    
    def test_user_str_method(self):
        """Test método __str__ del usuario"""
        expected = "Test User (test@example.com)"
        self.assertEqual(str(self.user), expected)
    
    def test_get_full_name(self):
        """Test método get_full_name"""
        self.assertEqual(self.user.get_full_name(), "Test User")
    
    def test_get_short_name(self):
        """Test método get_short_name"""
        self.assertEqual(self.user.get_short_name(), "Test")