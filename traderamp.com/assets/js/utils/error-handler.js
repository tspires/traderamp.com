/**
 * Error Handler Utility Module
 * @module ErrorHandler
 * @description Centralized error handling for the application
 */

(function(window, $) {
    'use strict';

    const ErrorHandler = {
        // Error types
        ERROR_TYPES: {
            NETWORK: 'NETWORK_ERROR',
            VALIDATION: 'VALIDATION_ERROR',
            SERVER: 'SERVER_ERROR',
            CLIENT: 'CLIENT_ERROR',
            UNKNOWN: 'UNKNOWN_ERROR'
        },

        // Error messages
        DEFAULT_MESSAGES: {
            NETWORK_ERROR: 'Unable to connect to the server. Please check your internet connection.',
            VALIDATION_ERROR: 'Please check the form and correct any errors.',
            SERVER_ERROR: 'Server error occurred. Please try again later.',
            CLIENT_ERROR: 'An error occurred. Please refresh the page and try again.',
            UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.'
        },

        /**
         * Handle AJAX errors
         * @param {Object} xhr - XMLHttpRequest object
         * @param {string} status - Status text
         * @param {Error} error - Error object
         * @param {Object} options - Additional options
         * @returns {Object} Formatted error response
         */
        handleAjaxError(xhr, status, error, options = {}) {
            const errorType = this.getErrorType(xhr.status);
            const errorMessage = this.getErrorMessage(xhr, errorType, options);
            
            const errorResponse = {
                type: errorType,
                status: xhr.status,
                statusText: xhr.statusText,
                message: errorMessage,
                details: this.extractErrorDetails(xhr),
                timestamp: new Date().toISOString()
            };

            if (options.logError !== false) {
                this.logError(errorResponse);
            }

            if (options.showNotification !== false) {
                this.showErrorNotification(errorMessage, options);
            }

            return errorResponse;
        },

        /**
         * Determine error type based on status code
         * @param {number} statusCode - HTTP status code
         * @returns {string} Error type
         */
        getErrorType(statusCode) {
            if (statusCode === 0) {
                return this.ERROR_TYPES.NETWORK;
            } else if (statusCode >= 400 && statusCode < 500) {
                return statusCode === 422 ? this.ERROR_TYPES.VALIDATION : this.ERROR_TYPES.CLIENT;
            } else if (statusCode >= 500) {
                return this.ERROR_TYPES.SERVER;
            }
            return this.ERROR_TYPES.UNKNOWN;
        },

        /**
         * Get appropriate error message
         * @param {Object} xhr - XMLHttpRequest object
         * @param {string} errorType - Type of error
         * @param {Object} options - Additional options
         * @returns {string} Error message
         */
        getErrorMessage(xhr, errorType, options) {
            // Try to get message from response
            if (xhr.responseJSON && xhr.responseJSON.message) {
                return xhr.responseJSON.message;
            }

            // Use custom message if provided
            if (options.customMessage) {
                return options.customMessage;
            }

            // Use default message for error type
            return this.DEFAULT_MESSAGES[errorType] || this.DEFAULT_MESSAGES.UNKNOWN_ERROR;
        },

        /**
         * Extract error details from response
         * @param {Object} xhr - XMLHttpRequest object
         * @returns {Object} Error details
         */
        extractErrorDetails(xhr) {
            const details = {};

            try {
                if (xhr.responseJSON) {
                    details.response = xhr.responseJSON;
                    
                    // Extract validation errors if present
                    if (xhr.responseJSON.errors) {
                        details.validationErrors = xhr.responseJSON.errors;
                    }
                } else if (xhr.responseText) {
                    details.responseText = xhr.responseText;
                }
            } catch (e) {
                details.parseError = 'Failed to parse error response';
            }

            return details;
        },

        /**
         * Log error for debugging
         * @param {Object} errorResponse - Error response object
         */
        logError(errorResponse) {
            if (window.console && console.error) {
                console.error('Application Error:', errorResponse);
            }
        },

        /**
         * Show error notification to user
         * @param {string} message - Error message
         * @param {Object} options - Display options
         */
        showErrorNotification(message, options = {}) {
            const $container = options.container || $('.error-container');
            const duration = options.duration || 5000;
            const type = options.type || 'danger';

            if (!$container.length) {
                console.warn('Error container not found');
                return;
            }

            const alertHtml = `
                <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
            `;

            const $alert = $(alertHtml);
            $container.html($alert);
            $alert.hide().fadeIn();

            if (duration > 0) {
                setTimeout(() => {
                    $alert.fadeOut(() => $alert.remove());
                }, duration);
            }
        },

        /**
         * Handle form validation errors
         * @param {jQuery} $form - Form element
         * @param {Object} errors - Validation errors
         * @param {Object} options - Display options
         */
        handleValidationErrors($form, errors, options = {}) {
            // Clear previous errors
            this.clearValidationErrors($form);

            // Display field-specific errors
            Object.keys(errors).forEach(fieldName => {
                const $field = $form.find(`[name="${fieldName}"]`);
                const errorMessage = Array.isArray(errors[fieldName]) 
                    ? errors[fieldName][0] 
                    : errors[fieldName];

                if ($field.length) {
                    this.showFieldError($field, errorMessage);
                }
            });

            // Show general validation message
            if (options.showGeneralMessage !== false) {
                this.showErrorNotification(
                    this.DEFAULT_MESSAGES.VALIDATION_ERROR,
                    { ...options, type: 'warning' }
                );
            }
        },

        /**
         * Show error for specific field
         * @param {jQuery} $field - Field element
         * @param {string} message - Error message
         */
        showFieldError($field, message) {
            $field.addClass('is-invalid');
            
            const $feedback = $(`<div class="invalid-feedback">${message}</div>`);
            $field.after($feedback);

            // Add error class to form group
            $field.closest('.form-group').addClass('has-error');
        },

        /**
         * Clear validation errors from form
         * @param {jQuery} $form - Form element
         */
        clearValidationErrors($form) {
            $form.find('.is-invalid').removeClass('is-invalid');
            $form.find('.invalid-feedback').remove();
            $form.find('.has-error').removeClass('has-error');
        },

        /**
         * Setup global error handler
         * @param {Object} options - Configuration options
         */
        setupGlobalErrorHandler(options = {}) {
            // Handle unhandled promise rejections
            window.addEventListener('unhandledrejection', (event) => {
                this.logError({
                    type: this.ERROR_TYPES.UNKNOWN,
                    message: 'Unhandled promise rejection',
                    error: event.reason,
                    timestamp: new Date().toISOString()
                });

                if (options.preventDefault !== false) {
                    event.preventDefault();
                }
            });

            // Handle global errors
            window.addEventListener('error', (event) => {
                this.logError({
                    type: this.ERROR_TYPES.UNKNOWN,
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno,
                    error: event.error,
                    timestamp: new Date().toISOString()
                });

                if (options.preventDefault !== false) {
                    event.preventDefault();
                }
            });

            // Setup AJAX error handler
            if ($ && $.ajaxSetup) {
                $.ajaxSetup({
                    error: (xhr, status, error) => {
                        if (!xhr.errorHandled) {
                            this.handleAjaxError(xhr, status, error, options.ajax || {});
                        }
                    }
                });
            }
        },

        /**
         * Create error boundary for function execution
         * @param {Function} fn - Function to execute
         * @param {Object} options - Error handling options
         * @returns {*} Function result or error
         */
        tryCatch(fn, options = {}) {
            try {
                return fn();
            } catch (error) {
                const errorResponse = {
                    type: this.ERROR_TYPES.UNKNOWN,
                    message: error.message,
                    stack: error.stack,
                    timestamp: new Date().toISOString()
                };

                if (options.logError !== false) {
                    this.logError(errorResponse);
                }

                if (options.rethrow) {
                    throw error;
                }

                return options.defaultValue !== undefined ? options.defaultValue : null;
            }
        },

        /**
         * Create async error boundary
         * @param {Function} asyncFn - Async function to execute
         * @param {Object} options - Error handling options
         * @returns {Promise} Promise with result or error
         */
        async tryCatchAsync(asyncFn, options = {}) {
            try {
                return await asyncFn();
            } catch (error) {
                const errorResponse = {
                    type: this.ERROR_TYPES.UNKNOWN,
                    message: error.message,
                    stack: error.stack,
                    timestamp: new Date().toISOString()
                };

                if (options.logError !== false) {
                    this.logError(errorResponse);
                }

                if (options.rethrow) {
                    throw error;
                }

                return options.defaultValue !== undefined ? options.defaultValue : null;
            }
        }
    };

    // Export to global scope
    window.ErrorHandler = ErrorHandler;

    // Also export as module if AMD/CommonJS is available
    if (typeof define === 'function' && define.amd) {
        define([], function() { return ErrorHandler; });
    } else if (typeof module === 'object' && module.exports) {
        module.exports = ErrorHandler;
    }

})(window, jQuery);