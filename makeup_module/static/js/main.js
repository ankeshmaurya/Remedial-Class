/**
 * Make-Up Class & Remedial Code Module
 * Main JavaScript File
 * Modern 2026 Edition
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all modules
    initSidebar();
    initTheme();
    initDropdowns();
    initNotifications();
    initAlerts();
    initForms();
    initCopyButtons();
    initModals();
    initAnimations();
});

// ===== SIDEBAR ===== //
function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    
    if (mobileMenuToggle && sidebar) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            document.querySelector('.main-content').classList.toggle('expanded');
        });
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        if (sidebar && sidebar.classList.contains('active')) {
            if (!sidebar.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        }
    });
}

// ===== THEME TOGGLE ===== //
function initTheme() {
    const themeToggle = document.querySelector('.theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Apply saved theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }
}

function updateThemeIcon(theme) {
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
}

// ===== DROPDOWNS ===== //
function initDropdowns() {
    const dropdownBtns = document.querySelectorAll('.user-btn, .dropdown-trigger');
    
    dropdownBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const dropdown = this.closest('.user-dropdown, .dropdown-container');
            const menu = dropdown.querySelector('.dropdown-menu');
            
            // Close all other dropdowns
            document.querySelectorAll('.dropdown-menu.active').forEach(m => {
                if (m !== menu) m.classList.remove('active');
            });
            
            menu.classList.toggle('active');
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown-menu.active').forEach(menu => {
            menu.classList.remove('active');
        });
    });
}

// ===== NOTIFICATIONS ===== //
function initNotifications() {
    const notificationBtn = document.querySelector('.notification-btn');
    
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            // Could open a notification panel or redirect
            window.location.href = this.dataset.href || '#';
        });
    }
    
    // Mark notifications as read
    document.querySelectorAll('.mark-read-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const notificationId = this.dataset.notificationId;
            markNotificationRead(notificationId);
        });
    });
}

async function markNotificationRead(notificationId) {
    try {
        const response = await fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const notificationItem = document.querySelector(`[data-notification-id="${notificationId}"]`).closest('.notification-item-full, .notification-item');
            if (notificationItem) {
                notificationItem.classList.remove('unread');
                notificationItem.querySelector('.mark-read-btn').remove();
            }
            updateNotificationBadge();
        }
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

function updateNotificationBadge() {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        const count = parseInt(badge.textContent) - 1;
        if (count <= 0) {
            badge.remove();
        } else {
            badge.textContent = count;
        }
    }
}

// ===== FLASH ALERTS ===== //
function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            dismissAlert(alert);
        }, 5000);
        
        // Close button
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => dismissAlert(alert));
        }
    });
}

function dismissAlert(alert) {
    alert.style.animation = 'slideOut 0.3s ease forwards';
    setTimeout(() => alert.remove(), 300);
}

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// ===== FORMS ===== //

// Global togglePassword function for onclick handlers
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const btn = input.closest('.password-input').querySelector('.toggle-password i');
    
    if (input.type === 'password') {
        input.type = 'text';
        if (btn) btn.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        input.type = 'password';
        if (btn) btn.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

function initForms() {
    // Password toggle visibility
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.closest('.password-input').querySelector('input');
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });
    });
    
    // Form validation
    document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
    
    // Real-time input validation
    document.querySelectorAll('input[required], select[required], textarea[required]').forEach(input => {
        input.addEventListener('blur', function() {
            validateInput(this);
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!validateInput(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateInput(input) {
    const value = input.value.trim();
    const type = input.type;
    let isValid = true;
    let errorMessage = '';
    
    // Required check
    if (!value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    if (isValid && type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // Password validation
    if (isValid && type === 'password' && value && input.dataset.minLength) {
        const minLength = parseInt(input.dataset.minLength);
        if (value.length < minLength) {
            isValid = false;
            errorMessage = `Password must be at least ${minLength} characters`;
        }
    }
    
    // Update UI
    const formGroup = input.closest('.form-group');
    const existingError = formGroup.querySelector('.form-error');
    
    if (!isValid) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        
        if (!existingError) {
            const errorEl = document.createElement('span');
            errorEl.className = 'form-error';
            errorEl.textContent = errorMessage;
            errorEl.style.cssText = 'color: var(--danger); font-size: 12px; margin-top: 4px; display: block;';
            formGroup.appendChild(errorEl);
        } else {
            existingError.textContent = errorMessage;
        }
    } else {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        if (existingError) {
            existingError.remove();
        }
    }
    
    return isValid;
}

// ===== COPY BUTTONS ===== //
function initCopyButtons() {
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const textToCopy = this.dataset.copy || this.previousElementSibling.textContent;
            copyToClipboard(textToCopy);
            showToast('Copied to clipboard!', 'success');
        });
    });
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    }
}

// ===== TOAST NOTIFICATIONS ===== //
function showToast(message, type = 'info') {
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                 type === 'error' ? 'fa-exclamation-circle' : 
                 type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
    
    toast.innerHTML = `<i class="fas ${icon}"></i><span>${message}</span>`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ===== MODALS ===== //
function initModals() {
    // Open modal buttons
    document.querySelectorAll('[data-modal-target]').forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.dataset.modalTarget;
            openModal(modalId);
        });
    });
    
    // Close modal buttons
    document.querySelectorAll('.modal-close, [data-modal-close]').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });
    
    // Close modal when clicking backdrop
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this);
            }
        });
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) {
                closeModal(activeModal);
            }
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modal) {
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ===== ANIMATIONS ===== //
function initAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.card, .stat-card, .class-card, .feature-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });
}

// Add animate-in styles
const animationStyle = document.createElement('style');
animationStyle.textContent = `
    .animate-in {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
`;
document.head.appendChild(animationStyle);

// ===== ATTENDANCE CODE ENTRY ===== //
function initCodeEntry() {
    const codeInput = document.getElementById('remedial-code-input');
    if (codeInput) {
        // Auto-format as user types (MUP-XXXXXX)
        codeInput.addEventListener('input', function(e) {
            let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
            
            if (value.length > 3 && !value.includes('-')) {
                value = value.substring(0, 3) + '-' + value.substring(3);
            }
            
            if (value.length > 10) {
                value = value.substring(0, 10);
            }
            
            e.target.value = value;
        });
    }
}

// Initialize code entry if on attendance page
document.addEventListener('DOMContentLoaded', initCodeEntry);

// ===== QR CODE SCANNER ===== //
let qrScanner = null;

function initQRScanner() {
    const qrReaderElement = document.getElementById('qr-reader');
    if (!qrReaderElement) return;
    
    // Check if Html5QrcodeScanner is available
    if (typeof Html5QrcodeScanner === 'undefined') {
        console.log('QR Scanner library not loaded');
        return;
    }
    
    qrScanner = new Html5QrcodeScanner('qr-reader', {
        fps: 10,
        qrbox: 250,
        rememberLastUsedCamera: true
    });
    
    qrScanner.render(onQRScanSuccess, onQRScanError);
}

function onQRScanSuccess(decodedText) {
    // Extract code from QR data
    const codeMatch = decodedText.match(/MUP-[A-Z0-9]{6}/);
    if (codeMatch) {
        const code = codeMatch[0];
        const codeInput = document.getElementById('remedial-code-input');
        if (codeInput) {
            codeInput.value = code;
        }
        
        // Close modal
        const modal = document.getElementById('qr-modal');
        if (modal) {
            closeModal(modal);
        }
        
        // Stop scanner
        if (qrScanner) {
            qrScanner.clear();
        }
        
        // Auto-submit or show success
        showToast('Code scanned successfully!', 'success');
    }
}

function onQRScanError(errorMessage) {
    // Handle scan errors silently
    console.log('QR Scan Error:', errorMessage);
}

// Start scanner when modal opens
document.addEventListener('DOMContentLoaded', function() {
    const qrModal = document.getElementById('qr-modal');
    if (qrModal) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.target.classList.contains('active')) {
                    initQRScanner();
                }
            });
        });
        
        observer.observe(qrModal, { attributes: true, attributeFilter: ['class'] });
    }
});

// ===== CHART.JS HELPERS ===== //
const chartColors = {
    primary: '#4F46E5',
    primaryLight: '#6366F1',
    success: '#10B981',
    warning: '#F59E0B',
    danger: '#EF4444',
    info: '#3B82F6',
    gray: '#6B7280'
};

function createLineChart(canvasId, labels, data, label = 'Data') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: chartColors.primary,
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function createBarChart(canvasId, labels, data, label = 'Data') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: chartColors.primary,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function createDoughnutChart(canvasId, labels, data, colors = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const defaultColors = [chartColors.primary, chartColors.success, chartColors.warning, chartColors.danger];
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors || defaultColors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// ===== ATTENDANCE MARKING ===== //
async function markAttendance(code) {
    const submitBtn = document.querySelector('.attendance-form button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : '';
    
    try {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
        }
        
        const response = await fetch('/student/api/mark-attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code: code })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showToast('Attendance marked successfully!', 'success');
            
            // Redirect after brief delay
            setTimeout(() => {
                window.location.href = data.redirect || '/student/attendance-success';
            }, 1000);
        } else {
            showToast(data.message || 'Failed to mark attendance', 'error');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        }
    } catch (error) {
        console.error('Error marking attendance:', error);
        showToast('An error occurred. Please try again.', 'error');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
}

// ===== SCHEDULE RECOMMENDATIONS ===== //
function applyRecommendation(date, startTime, endTime) {
    const dateInput = document.getElementById('class-date');
    const startInput = document.getElementById('start-time');
    const endInput = document.getElementById('end-time');
    
    if (dateInput) dateInput.value = date;
    if (startInput) startInput.value = startTime;
    if (endInput) endInput.value = endTime;
    
    // Scroll to form
    const form = document.querySelector('.schedule-form, .class-form');
    if (form) {
        form.scrollIntoView({ behavior: 'smooth' });
    }
    
    showToast('Recommendation applied!', 'success');
    
    // Update UI to show applied state
    document.querySelectorAll('.recommendation-item').forEach(item => {
        item.classList.remove('applied');
    });
    event.target.closest('.recommendation-item').classList.add('applied');
}

// ===== DATA TABLE SORTING ===== //
function initTableSorting() {
    document.querySelectorAll('.data-table th[data-sortable]').forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const index = Array.from(this.parentNode.children).indexOf(this);
            const direction = this.dataset.sortDir === 'asc' ? 'desc' : 'asc';
            
            rows.sort((a, b) => {
                const aVal = a.children[index].textContent.trim();
                const bVal = b.children[index].textContent.trim();
                
                // Check if numeric
                const aNum = parseFloat(aVal);
                const bNum = parseFloat(bVal);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return direction === 'asc' ? aNum - bNum : bNum - aNum;
                }
                
                return direction === 'asc' 
                    ? aVal.localeCompare(bVal) 
                    : bVal.localeCompare(aVal);
            });
            
            // Update sort indicators
            table.querySelectorAll('th').forEach(th => {
                th.classList.remove('sorted-asc', 'sorted-desc');
                th.removeAttribute('data-sort-dir');
            });
            
            this.classList.add(`sorted-${direction}`);
            this.dataset.sortDir = direction;
            
            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

document.addEventListener('DOMContentLoaded', initTableSorting);

// ===== SEARCH/FILTER FUNCTIONALITY ===== //
function initSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            const query = this.value.toLowerCase();
            const items = document.querySelectorAll('[data-searchable]');
            
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(query) ? '' : 'none';
            });
        }, 300));
    }
}

document.addEventListener('DOMContentLoaded', initSearch);

// ===== UTILITY FUNCTIONS ===== //
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatDate(date) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(date).toLocaleDateString('en-US', options);
}

function formatTime(time) {
    return new Date(`2000-01-01T${time}`).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

// ===== EXPORT FUNCTIONS ===== //
async function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('th, td');
        const rowData = Array.from(cells).map(cell => {
            let text = cell.textContent.trim();
            // Escape quotes and wrap in quotes
            text = `"${text.replace(/"/g, '""')}"`;
            return text;
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    link.href = URL.createObjectURL(blob);
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    
    showToast('Export completed!', 'success');
}

// ===== CONFIRMATION DIALOGS ===== //
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Handle delete/cancel buttons
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-confirm]').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});

// ===== LIVE TIME UPDATE ===== //
function updateLiveTime() {
    const liveTimeElements = document.querySelectorAll('.live-time');
    liveTimeElements.forEach(el => {
        el.textContent = new Date().toLocaleTimeString();
    });
}

// Update every second if live time elements exist
if (document.querySelector('.live-time')) {
    setInterval(updateLiveTime, 1000);
    updateLiveTime();
}

// ===== CLASS STATUS HELPERS ===== //
function getStatusBadgeClass(status) {
    const statusMap = {
        'scheduled': 'badge-info',
        'ongoing': 'badge-warning',
        'completed': 'badge-success',
        'cancelled': 'badge-danger'
    };
    return statusMap[status.toLowerCase()] || 'badge-primary';
}

function getRushLevelClass(level) {
    const levelMap = {
        'low': 'rush-low',
        'medium': 'rush-medium',
        'high': 'rush-high'
    };
    return levelMap[level.toLowerCase()] || 'rush-low';
}

// ===== MAKE FUNCTIONS GLOBALLY AVAILABLE ===== //
window.MakeUpModule = {
    showToast,
    openModal,
    closeModal,
    copyToClipboard,
    markAttendance,
    applyRecommendation,
    exportToCSV,
    confirmAction,
    createLineChart,
    createBarChart,
    createDoughnutChart,
    formatDate,
    formatTime
};
