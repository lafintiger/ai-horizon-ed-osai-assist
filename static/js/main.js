// AI-Horizon Ed Platform - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);

    // Add fade-in animation to cards
    var cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        card.style.animationDelay = (index * 0.1) + 's';
        card.classList.add('fade-in');
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Loading state for buttons
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function() {
            if (this.getAttribute('data-loading') === 'true') {
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
            }
        });
    });

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Back to top button
    var backToTopBtn = document.createElement('button');
    backToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopBtn.className = 'btn btn-primary btn-floating';
    backToTopBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: none;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;
    document.body.appendChild(backToTopBtn);

    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.display = 'block';
        } else {
            backToTopBtn.style.display = 'none';
        }
    });

    backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Progress tracking
    if (typeof Storage !== "undefined") {
        // Save progress to localStorage
        window.saveProgress = function(skillId, resourceId, progress) {
            var progressData = JSON.parse(localStorage.getItem('aiHorizonProgress') || '{}');
            if (!progressData[skillId]) {
                progressData[skillId] = {};
            }
            progressData[skillId][resourceId] = {
                progress: progress,
                timestamp: new Date().toISOString()
            };
            localStorage.setItem('aiHorizonProgress', JSON.stringify(progressData));
        };

        // Load progress from localStorage
        window.loadProgress = function(skillId, resourceId) {
            var progressData = JSON.parse(localStorage.getItem('aiHorizonProgress') || '{}');
            if (progressData[skillId] && progressData[skillId][resourceId]) {
                return progressData[skillId][resourceId];
            }
            return null;
        };

        // Display progress indicators
        var progressBars = document.querySelectorAll('.progress-bar[data-skill-id][data-resource-id]');
        progressBars.forEach(function(bar) {
            var skillId = bar.getAttribute('data-skill-id');
            var resourceId = bar.getAttribute('data-resource-id');
            var progress = window.loadProgress(skillId, resourceId);
            if (progress) {
                bar.style.width = progress.progress + '%';
                bar.setAttribute('aria-valuenow', progress.progress);
            }
        });
    }

    // API utilities
    window.apiRequest = function(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const finalOptions = { ...defaultOptions, ...options };

        return fetch(endpoint, finalOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('API request failed:', error);
                throw error;
            });
    };

    // Skills search functionality
    window.searchSkills = function(searchTerm, category = '') {
        return window.apiRequest(`/api/skills?search=${encodeURIComponent(searchTerm)}&category=${encodeURIComponent(category)}`);
    };

    // Resource management
    window.markResourceCompleted = function(skillId, resourceId) {
        window.saveProgress(skillId, resourceId, 100);
        
        // Visual feedback
        var card = document.querySelector(`[data-resource-id="${resourceId}"]`);
        if (card) {
            card.classList.add('completed');
            var badge = card.querySelector('.badge');
            if (badge) {
                badge.textContent = 'Completed';
                badge.className = 'badge bg-success';
            }
        }

        // Show success message
        showNotification('Resource marked as completed!', 'success');
    };

    // Notification system
    window.showNotification = function(message, type = 'info') {
        var notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1050;
            min-width: 300px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(function() {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    };

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            var searchInput = document.getElementById('skillSearch');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape to close modals
        if (e.key === 'Escape') {
            var modals = document.querySelectorAll('.modal.show');
            modals.forEach(function(modal) {
                var bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });

    // Print functionality
    window.printPage = function() {
        window.print();
    };

    // Export functionality
    window.exportData = function(type = 'json') {
        var data = {
            skills: [],
            timestamp: new Date().toISOString(),
            version: '2.0.0'
        };

        // This would be populated with actual data
        var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = `ai-horizon-export-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    // Theme toggle (if implemented)
    window.toggleTheme = function() {
        document.body.classList.toggle('dark-theme');
        localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
    };

    // Load saved theme
    var savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }

    // Performance monitoring
    window.addEventListener('load', function() {
        setTimeout(function() {
            var perfData = performance.getEntriesByType('navigation')[0];
            if (perfData) {
                var loadTime = perfData.loadEventEnd - perfData.loadEventStart;
                console.log('Page load time:', loadTime + 'ms');
                
                // Report slow loading (>3 seconds)
                if (loadTime > 3000) {
                    console.warn('Slow page load detected:', loadTime + 'ms');
                }
            }
        }, 0);
    });

    console.log('AI-Horizon Ed Platform initialized successfully');
});

// Utility functions available globally
window.AIHorizonEd = {
    version: '2.0.0',
    
    // Format duration in minutes to human readable
    formatDuration: function(minutes) {
        if (minutes < 60) {
            return minutes + ' min';
        } else if (minutes < 1440) {
            var hours = Math.floor(minutes / 60);
            var remainingMinutes = minutes % 60;
            return hours + 'h' + (remainingMinutes > 0 ? ' ' + remainingMinutes + 'm' : '');
        } else {
            var days = Math.floor(minutes / 1440);
            var remainingHours = Math.floor((minutes % 1440) / 60);
            return days + 'd' + (remainingHours > 0 ? ' ' + remainingHours + 'h' : '');
        }
    },

    // Format urgency score
    formatUrgencyScore: function(score) {
        if (score >= 8) return 'Critical';
        if (score >= 6) return 'High';
        if (score >= 4) return 'Medium';
        return 'Low';
    },

    // Get difficulty color
    getDifficultyColor: function(level) {
        switch (level?.toLowerCase()) {
            case 'beginner': return 'success';
            case 'intermediate': return 'warning';
            case 'advanced': return 'danger';
            default: return 'secondary';
        }
    }
}; 