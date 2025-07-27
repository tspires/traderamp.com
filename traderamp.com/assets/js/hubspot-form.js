/**
 * HubSpot Form Integration
 * Handles HubSpot form initialization and customization
 */

(function(window, document, $) {
    'use strict';

    const HubSpotFormHandler = {
        // Configuration
        config: {
            portalId: '242471098', // Replace with actual portal ID
            formId: 'a031a33a-709c-4970-8679-5064e825987d',     // Replace with actual form ID
            region: 'na2',
            target: '.hs-form-frame',
            cssRequired: true,
            cssClass: 'traderamp-hubspot-form',
            onFormReady: null,
            onFormSubmitted: null
        },

        /**
         * Initialize HubSpot form
         */
        init() {
            // Wait for HubSpot script to load
            this.waitForHubSpot(() => {
                this.createForm();
            });

            // Listen for form events
            this.bindEvents();
        },

        /**
         * Wait for HubSpot global object
         */
        waitForHubSpot(callback) {
            if (window.hbspt && window.hbspt.forms) {
                callback();
            } else {
                // Check every 100ms for HubSpot to be ready
                setTimeout(() => this.waitForHubSpot(callback), 100);
            }
        },

        /**
         * Create HubSpot form
         */
        createForm() {
            const formContainer = document.querySelector(this.config.target);
            
            if (!formContainer) {
                console.error('HubSpot form container not found');
                return;
            }

            // Get configuration from data attributes if available
            const portalId = formContainer.getAttribute('data-portal-id') || this.config.portalId;
            const formId = formContainer.getAttribute('data-form-id') || this.config.formId;
            const region = formContainer.getAttribute('data-region') || this.config.region;

            // Validate configuration
            if (portalId === 'YOUR-HUBSPOT-PORTAL-ID' || formId === 'YOUR-HUBSPOT-FORM-ID') {
                console.error('Please configure your HubSpot Portal ID and Form ID');
                formContainer.innerHTML = '<p style="color: red; text-align: center;">Form configuration needed. Please contact administrator.</p>';
                return;
            }

            // Create the form
            window.hbspt.forms.create({
                region: region,
                portalId: portalId,
                formId: formId,
                target: this.config.target,
                cssRequired: this.config.cssRequired,
                cssClass: this.config.cssClass,
                
                // Callbacks
                onFormReady: (form) => {
                    this.onFormReady(form);
                    if (typeof this.config.onFormReady === 'function') {
                        this.config.onFormReady(form);
                    }
                },
                
                onFormSubmitted: (form) => {
                    this.onFormSubmitted(form);
                    if (typeof this.config.onFormSubmitted === 'function') {
                        this.config.onFormSubmitted(form);
                    }
                },

                // Custom submit button text
                submitButtonClass: 'hs-button btn btn--primary btn--rounded',
                
                // Error message customization
                errorMessageClass: 'hs-error-msg alert alert-danger',
                
                // Success message
                inlineMessage: 'Thank you for your interest! We\'ll contact you within 24 hours to schedule your call.',
                
                // Form styling
                css: ''
            });
        },

        /**
         * Form ready callback
         */
        onFormReady(form) {
            // Add custom classes to form elements
            const formElement = document.querySelector('.hs-form');
            if (formElement) {
                // Add Bootstrap classes to inputs
                const inputs = formElement.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    if (!input.classList.contains('hs-input')) {
                        input.classList.add('hs-input');
                    }
                    input.classList.add('form-control');
                });

                // Style submit button
                const submitButton = formElement.querySelector('input[type="submit"]');
                if (submitButton) {
                    submitButton.className = 'btn btn--primary btn--rounded btn--cta-large';
                    
                    // Update button text if needed
                    if (submitButton.value === 'Submit') {
                        submitButton.value = 'Schedule Your Free 25-Minute Call';
                    }
                }
            }

            // Track form view in analytics
            this.trackEvent('Form Viewed');
        },

        /**
         * Form submitted callback
         */
        onFormSubmitted(form) {
            // Track conversion
            this.trackConversion();

            // Show custom success message if needed
            const formContainer = document.querySelector(this.config.target);
            if (formContainer) {
                // Scroll to form
                $('html, body').animate({
                    scrollTop: $(formContainer).offset().top - 100
                }, 500);
            }
        },

        /**
         * Bind additional events
         */
        bindEvents() {
            // Track form field interactions
            $(document).on('focus', '.hs-form input, .hs-form select, .hs-form textarea', function() {
                const fieldName = $(this).attr('name') || 'unknown';
                HubSpotFormHandler.trackEvent('Form Field Focused', { field: fieldName });
            });
        },

        /**
         * Track events in analytics
         */
        trackEvent(action, data = {}) {
            // Google Analytics
            if (typeof gtag !== 'undefined') {
                gtag('event', action, {
                    'event_category': 'HubSpot Form',
                    'event_label': 'Schedule Call Form',
                    ...data
                });
            }

            // Facebook Pixel
            if (typeof fbq !== 'undefined' && action === 'Form Viewed') {
                fbq('track', 'ViewContent', {
                    content_name: 'Schedule Call Form'
                });
            }
        },

        /**
         * Track conversion
         */
        trackConversion() {
            // Google Analytics
            if (typeof gtag !== 'undefined') {
                gtag('event', 'conversion', {
                    'event_category': 'Lead',
                    'event_label': 'HubSpot Form Submission'
                });
            }

            // Facebook Pixel
            if (typeof fbq !== 'undefined') {
                fbq('track', 'Lead', {
                    content_name: 'Schedule Call Form'
                });
            }
        },

        /**
         * Update configuration
         */
        setConfig(options) {
            this.config = { ...this.config, ...options };
        }
    };

    // Initialize when DOM is ready
    $(document).ready(() => {
        // Check if HubSpot form container exists
        if (document.querySelector('.hs-form-frame')) {
            HubSpotFormHandler.init();
        }
    });

    // Export for external use
    window.HubSpotFormHandler = HubSpotFormHandler;

})(window, document, jQuery);