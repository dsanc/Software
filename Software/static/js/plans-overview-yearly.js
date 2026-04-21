/**
 * Plans Overview JavaScript Module
 * Handles interactions for the subscription plans overview page
 */

// ===== GLOBAL VARIABLES =====
let isDebug = false;

// ===== TRACKING FUNCTIONS =====
function trackModuleClick(moduleName) {
    /**
     * Track when a user clicks on a module tab
     * @param {string} moduleName - Name of the module being clicked
     */
    if (isDebug) {
        console.log(`Module clicked: ${moduleName}`);
    }
    
    // TODO: Implement analytics tracking when available
    // Example: gtag('event', 'module_click', { module_name: moduleName });
    
    // Update URL hash for direct linking
    if (history.pushState) {
        const newUrl = `${window.location.pathname}#module-${moduleName}`;
        history.pushState(null, null, newUrl);
    }
    
    // Store last viewed module in localStorage
    try {
        localStorage.setItem('lastViewedModule', moduleName);
    } catch (e) {
        // localStorage might be disabled
        if (isDebug) console.warn('Could not save to localStorage:', e);
    }
}

function trackPlanInteraction(action, planId, planName, moduleName) {
    /**
     * Track plan-related interactions
     * @param {string} action - The action performed (view, click, select, etc.)
     * @param {string} planId - ID of the plan
     * @param {string} planName - Name of the plan
     * @param {string} moduleName - Name of the module
     */
    if (isDebug) {
        console.log(`Plan ${action}:`, { planId, planName, moduleName });
    }
    
    // TODO: Implement analytics tracking when available
    // Example: gtag('event', 'plan_interaction', {
    //     action: action,
    //     plan_id: planId,
    //     plan_name: planName,
    //     module_name: moduleName
    // });
}

// ===== UTILITY FUNCTIONS =====
function debounce(func, wait, immediate) {
    /**
     * Debounce function to limit how often a function can be called
     */
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

function getModuleFromHash() {
    /**
     * Extract module name from URL hash
     * @returns {string|null} Module name or null if not found
     */
    const hash = window.location.hash;
    if (hash && hash.startsWith('#module-')) {
        return hash.substring(8); // Remove '#module-'
    }
    return null;
}

function activateModuleFromHash() {
    /**
     * Activate the correct module tab based on URL hash
     */
    const moduleName = getModuleFromHash();
    if (moduleName) {
        const tabButton = document.querySelector(`[data-bs-target="#module-${moduleName}"]`);
        if (tabButton) {
            // Use Bootstrap's tab API to show the tab
            const tab = new bootstrap.Tab(tabButton);
            tab.show();
            trackModuleClick(moduleName);
        }
    }
}

function restoreLastViewedModule() {
    /**
     * Restore the last viewed module from localStorage
     */
    try {
        const lastModule = localStorage.getItem('lastViewedModule');
        if (lastModule && !getModuleFromHash()) {
            // Only restore if there's no hash in URL
            const tabButton = document.querySelector(`[data-bs-target="#module-${lastModule}"]`);
            if (tabButton) {
                const tab = new bootstrap.Tab(tabButton);
                tab.show();
            }
        }
    } catch (e) {
        if (isDebug) console.warn('Could not restore from localStorage:', e);
    }
}

// ===== PLAN INTERACTION HANDLERS =====
function handlePlanHover(planElement, planData) {
    /**
     * Handle plan card hover effects
     */
    planElement.classList.add('plan-hover-active');
    trackPlanInteraction('hover', planData.id, planData.name, planData.module);
}

function handlePlanLeave(planElement) {
    /**
     * Handle plan card hover leave
     */
    planElement.classList.remove('plan-hover-active');
}

function handlePlanClick(planElement, planData) {
    /**
     * Handle plan card click
     */
    trackPlanInteraction('click', planData.id, planData.name, planData.module);
    
    // Add visual feedback
    planElement.classList.add('plan-clicked');
    setTimeout(() => {
        planElement.classList.remove('plan-clicked');
    }, 200);
}

// ===== COMPARISON TABLE FUNCTIONS =====
function initializeComparisonTable() {
    /**
     * Initialize comparison table interactions
     */
    const tables = document.querySelectorAll('.comparison-table table');
    tables.forEach(table => {
        // Add hover effects to table rows
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.classList.add('table-row-hover');
            });
            row.addEventListener('mouseleave', function() {
                this.classList.remove('table-row-hover');
            });
        });
    });
}

// ===== RESPONSIVE HELPERS =====
function updateMobileView() {
    /**
     * Update view for mobile devices
     */
    const isMobile = window.innerWidth < 768;
    const planCards = document.querySelectorAll('.plan-card');
    
    planCards.forEach(card => {
        if (isMobile) {
            card.classList.add('mobile-optimized');
        } else {
            card.classList.remove('mobile-optimized');
        }
    });
}

// ===== INITIALIZATION =====
function initializePlansOverview() {
    /**
     * Initialize all plan overview functionality
     */
    console.log('Plans Overview module initialized');
    
    // Check for debug mode
    isDebug = new URLSearchParams(window.location.search).has('debug');
    
    // Initialize comparison tables
    initializeComparisonTable();
    
    // Handle URL hash on load
    activateModuleFromHash();
    
    // Restore last viewed module if no hash
    restoreLastViewedModule();
    
    // Initialize plan card interactions
    const planCards = document.querySelectorAll('.plan-card');
    planCards.forEach(card => {
        const planData = {
            id: card.dataset.planId || 'unknown',
            name: card.dataset.planName || 'Unknown Plan',
            module: card.closest('[data-module]')?.dataset.module || 'unknown'
        };
        
        card.addEventListener('mouseenter', () => handlePlanHover(card, planData));
        card.addEventListener('mouseleave', () => handlePlanLeave(card));
        card.addEventListener('click', () => handlePlanClick(card, planData));
    });
    
    // Handle window resize
    const debouncedResize = debounce(updateMobileView, 250);
    window.addEventListener('resize', debouncedResize);
    
    // Initial mobile view update
    updateMobileView();
    
    // Handle hash changes (browser back/forward)
    window.addEventListener('hashchange', activateModuleFromHash);
    
    // Handle tab changes
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tabButton => {
        tabButton.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('data-bs-target');
            if (target && target.startsWith('#module-')) {
                const moduleName = target.substring(8); // Remove '#module-'
                trackModuleClick(moduleName);
            }
        });
    });
}

// ===== CSS CLASSES FOR INTERACTIONS =====
const dynamicStyles = `
    .plan-hover-active {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }
    
    .plan-clicked {
        transform: scale(0.98);
        transition: transform 0.1s ease;
    }
    
    .table-row-hover {
        background-color: rgba(102, 126, 234, 0.05) !important;
    }
    
    .mobile-optimized {
        margin-bottom: 1.5rem;
    }
    
    .mobile-optimized .plan-features {
        max-height: 200px;
        overflow-y: auto;
    }
`;

// Add dynamic styles to document
if (typeof document !== 'undefined') {
    const styleElement = document.createElement('style');
    styleElement.textContent = dynamicStyles;
    document.head.appendChild(styleElement);
}

// ===== AUTO-INITIALIZATION =====
// Initialize when DOM is ready
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializePlansOverview);
    } else {
        // DOM is already ready
        initializePlansOverview();
    }
}

// ===== EXPORT FUNCTIONS FOR GLOBAL ACCESS =====
if (typeof window !== 'undefined') {
    window.trackModuleClick = trackModuleClick;
    window.trackPlanInteraction = trackPlanInteraction;
    window.initializePlansOverview = initializePlansOverview;
}