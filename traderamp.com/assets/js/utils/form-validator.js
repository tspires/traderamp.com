/**
 * Form Validation Utility Module
 * @module FormValidator
 * @description Client-side form validation with clean code principles
 */

(function(window, $) {
    'use strict';

    const FormValidator = {
        // Validation rules
        RULES: {
            required: {
                test: (value) => value !== null && value !== undefined && value.toString().trim() !== '',
                message: 'This field is required'
            },
            email: {
                test: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
                message: 'Please enter a valid email address'
            },
            phone: {
                test: (value) => /^[\+]?[1-9][\d]{0,15}$/.test(value.replace(/[\s\-\(\)]/g, '')),
                message: 'Please enter a valid phone number'
            },
            url: {
                test: (value) => /^https?:\/\/.+/.test(value),
                message: 'Please enter a valid URL'
            },
            minLength: {
                test: (value, param) => value.length >= param,
                message: (param) => `Must be at least ${param} characters long`
            },
            maxLength: {
                test: (value, param) => value.length <= param,
                message: (param) => `Must be no more than ${param} characters long`
            },
            pattern: {
                test: (value, param) => new RegExp(param).test(value),
                message: 'Please enter a value in the correct format'
            },
            number: {
                test: (value) => !isNaN(value) && !isNaN(parseFloat(value)),
                message: 'Please enter a valid number'
            },
            integer: {
                test: (value) => Number.isInteger(Number(value)),
                message: 'Please enter a valid integer'
            },
            min: {
                test: (value, param) => Number(value) >= param,
                message: (param) => `Must be at least ${param}`
            },
            max: {
                test: (value, param) => Number(value) <= param,
                message: (param) => `Must be no more than ${param}`
            }
        },

        // Default configuration
        DEFAULT_CONFIG: {
            validateOnBlur: true,
            validateOnInput: false,
            showErrorsInline: true,
            stopOnFirstError: false,
            errorClass: 'is-invalid',
            successClass: 'is-valid',
            errorContainerClass: 'invalid-feedback'
        },

        /**
         * Validate a form
         * @param {jQuery|HTMLElement|string} form - Form element or selector
         * @param {Object} config - Validation configuration
         * @returns {Object} Validation result
         */
        validateForm(form, config = {}) {
            const $form = $(form);
            const settings = { ...this.DEFAULT_CONFIG, ...config };
            const results = {
                isValid: true,
                errors: {},
                fields: {}
            };

            if (!$form.length) {
                throw new Error('Form not found');
            }

            // Get all form fields
            const $fields = $form.find('input, textarea, select').not('[type="submit"], [type="button"]');

            $fields.each((index, field) => {
                const $field = $(field);
                const fieldResult = this.validateField($field, settings);
                
                results.fields[$field.attr('name') || index] = fieldResult;

                if (!fieldResult.isValid) {
                    results.isValid = false;
                    results.errors[$field.attr('name') || index] = fieldResult.errors;

                    if (settings.stopOnFirstError) {
                        return false; // Break out of each loop
                    }
                }
            });

            return results;
        },

        /**
         * Validate a single field
         * @param {jQuery|HTMLElement} field - Field element
         * @param {Object} config - Validation configuration
         * @returns {Object} Field validation result
         */
        validateField(field, config = {}) {
            const $field = $(field);
            const settings = { ...this.DEFAULT_CONFIG, ...config };
            const value = $field.val();
            const rules = this.getFieldRules($field);
            
            const result = {
                isValid: true,
                errors: [],
                value: value
            };

            // Skip validation if field is disabled
            if ($field.is(':disabled')) {
                return result;
            }

            // Validate each rule
            rules.forEach(rule => {
                const ruleResult = this.validateRule(value, rule);
                if (!ruleResult.isValid) {
                    result.isValid = false;
                    result.errors.push(ruleResult.message);
                }
            });

            // Update field UI
            if (settings.showErrorsInline) {
                this.updateFieldUI($field, result, settings);
            }

            return result;
        },

        /**
         * Get validation rules for a field
         * @param {jQuery} $field - Field element
         * @returns {Array} Array of validation rules
         */
        getFieldRules($field) {
            const rules = [];
            
            // Required rule
            if ($field.is('[required]') || $field.data('required')) {
                rules.push({ name: 'required' });
            }

            // HTML5 input type rules
            const type = $field.attr('type');
            if (type === 'email') {
                rules.push({ name: 'email' });
            } else if (type === 'tel') {
                rules.push({ name: 'phone' });
            } else if (type === 'url') {
                rules.push({ name: 'url' });
            } else if (type === 'number') {
                rules.push({ name: 'number' });
            }

            // Pattern rule
            const pattern = $field.attr('pattern') || $field.data('pattern');
            if (pattern) {
                rules.push({ name: 'pattern', param: pattern });
            }

            // Length rules
            const minLength = $field.attr('minlength') || $field.data('min-length');
            if (minLength) {
                rules.push({ name: 'minLength', param: parseInt(minLength) });
            }

            const maxLength = $field.attr('maxlength') || $field.data('max-length');
            if (maxLength) {
                rules.push({ name: 'maxLength', param: parseInt(maxLength) });
            }

            // Number range rules
            const min = $field.attr('min') || $field.data('min');
            if (min !== undefined) {
                rules.push({ name: 'min', param: parseFloat(min) });
            }

            const max = $field.attr('max') || $field.data('max');
            if (max !== undefined) {
                rules.push({ name: 'max', param: parseFloat(max) });
            }

            // Custom validation rules from data attributes
            const customRules = $field.data('validate');
            if (customRules) {
                const ruleArray = customRules.split('|');
                ruleArray.forEach(ruleString => {
                    const [ruleName, param] = ruleString.split(':');
                    if (this.RULES[ruleName]) {
                        rules.push({ 
                            name: ruleName, 
                            param: param ? this.parseRuleParam(param) : undefined 
                        });
                    }
                });
            }

            return rules;
        },

        /**
         * Parse rule parameter from string
         * @param {string} param - Parameter string
         * @returns {*} Parsed parameter
         */
        parseRuleParam(param) {
            // Try to parse as number
            if (!isNaN(param)) {
                return parseFloat(param);
            }
            
            // Return as string
            return param;
        },

        /**
         * Validate a value against a rule
         * @param {*} value - Value to validate
         * @param {Object} rule - Validation rule
         * @returns {Object} Rule validation result
         */
        validateRule(value, rule) {
            const ruleDefinition = this.RULES[rule.name];
            
            if (!ruleDefinition) {
                return { isValid: false, message: `Unknown validation rule: ${rule.name}` };
            }

            // Skip validation for empty values except required rule
            if (rule.name !== 'required' && (!value || value.toString().trim() === '')) {
                return { isValid: true };
            }

            const isValid = ruleDefinition.test(value, rule.param);
            const message = isValid ? '' : this.getRuleMessage(ruleDefinition, rule);

            return { isValid, message };
        },

        /**
         * Get error message for a rule
         * @param {Object} ruleDefinition - Rule definition
         * @param {Object} rule - Rule instance
         * @returns {string} Error message
         */
        getRuleMessage(ruleDefinition, rule) {
            if (typeof ruleDefinition.message === 'function') {
                return ruleDefinition.message(rule.param);
            }
            return ruleDefinition.message;
        },

        /**
         * Update field UI based on validation result
         * @param {jQuery} $field - Field element
         * @param {Object} result - Validation result
         * @param {Object} settings - Configuration settings
         */
        updateFieldUI($field, result, settings) {
            // Remove existing validation classes and messages
            $field.removeClass(`${settings.errorClass} ${settings.successClass}`);
            $field.siblings(`.${settings.errorContainerClass}`).remove();

            if (result.isValid) {
                $field.addClass(settings.successClass);
            } else {
                $field.addClass(settings.errorClass);
                
                // Add error message
                const errorMessage = result.errors.join(', ');
                const $errorContainer = $(`<div class="${settings.errorContainerClass}">${errorMessage}</div>`);
                $field.after($errorContainer);
            }
        },

        /**
         * Setup automatic validation for a form
         * @param {jQuery|HTMLElement|string} form - Form element or selector
         * @param {Object} config - Configuration options
         * @returns {Object} Form validator instance
         */
        setupForm(form, config = {}) {
            const $form = $(form);
            const settings = { ...this.DEFAULT_CONFIG, ...config };

            if (!$form.length) {
                throw new Error('Form not found');
            }

            // Store settings on form
            $form.data('validator-settings', settings);

            // Bind events
            if (settings.validateOnBlur) {
                $form.on('blur', 'input, textarea, select', (event) => {
                    this.validateField($(event.target), settings);
                });
            }

            if (settings.validateOnInput) {
                $form.on('input', 'input, textarea', (event) => {
                    // Debounce input validation
                    const $field = $(event.target);
                    clearTimeout($field.data('validation-timeout'));
                    $field.data('validation-timeout', setTimeout(() => {
                        this.validateField($field, settings);
                    }, 300));
                });
            }

            // Validate on form submission
            $form.on('submit', (event) => {
                const validationResult = this.validateForm($form, settings);
                
                if (!validationResult.isValid) {
                    event.preventDefault();
                    
                    // Focus first invalid field
                    const firstErrorField = Object.keys(validationResult.errors)[0];
                    const $firstField = $form.find(`[name="${firstErrorField}"]`);
                    if ($firstField.length) {
                        $firstField.focus();
                    }
                    
                    // Trigger validation failed event
                    $form.trigger('validation:failed', [validationResult]);
                } else {
                    // Trigger validation passed event
                    $form.trigger('validation:passed', [validationResult]);
                }
            });

            return {
                validate: () => this.validateForm($form, settings),
                validateField: (fieldName) => {
                    const $field = $form.find(`[name="${fieldName}"]`);
                    return this.validateField($field, settings);
                },
                clearErrors: () => this.clearFormErrors($form, settings),
                destroy: () => this.destroyForm($form)
            };
        },

        /**
         * Clear all validation errors from a form
         * @param {jQuery} $form - Form element
         * @param {Object} settings - Configuration settings
         */
        clearFormErrors($form, settings) {
            $form.find(`.${settings.errorClass}, .${settings.successClass}`)
                 .removeClass(`${settings.errorClass} ${settings.successClass}`);
            $form.find(`.${settings.errorContainerClass}`).remove();
        },

        /**
         * Destroy form validation
         * @param {jQuery} $form - Form element
         */
        destroyForm($form) {
            $form.off('blur submit input');
            $form.removeData('validator-settings');
            this.clearFormErrors($form, this.DEFAULT_CONFIG);
        },

        /**
         * Add custom validation rule
         * @param {string} name - Rule name
         * @param {Function} testFunction - Validation function
         * @param {string|Function} message - Error message
         */
        addRule(name, testFunction, message) {
            this.RULES[name] = {
                test: testFunction,
                message: message
            };
        },

        /**
         * Validate email format
         * @param {string} email - Email to validate
         * @returns {boolean} Is valid email
         */
        isValidEmail(email) {
            return this.RULES.email.test(email);
        },

        /**
         * Validate phone number format
         * @param {string} phone - Phone number to validate
         * @returns {boolean} Is valid phone
         */
        isValidPhone(phone) {
            return this.RULES.phone.test(phone);
        },

        /**
         * Sanitize input value
         * @param {string} value - Input value
         * @param {Object} options - Sanitization options
         * @returns {string} Sanitized value
         */
        sanitize(value, options = {}) {
            if (typeof value !== 'string') {
                return value;
            }

            let sanitized = value;

            // Trim whitespace
            if (options.trim !== false) {
                sanitized = sanitized.trim();
            }

            // Remove HTML tags
            if (options.stripTags) {
                sanitized = sanitized.replace(/<[^>]*>/g, '');
            }

            // Escape HTML entities
            if (options.escapeHtml) {
                const div = document.createElement('div');
                div.textContent = sanitized;
                sanitized = div.innerHTML;
            }

            return sanitized;
        }
    };

    // Export to global scope
    window.FormValidator = FormValidator;

    // jQuery plugin
    if ($) {
        $.fn.validator = function(config) {
            return this.each(function() {
                FormValidator.setupForm(this, config);
            });
        };
    }

    // Also export as module if AMD/CommonJS is available
    if (typeof define === 'function' && define.amd) {
        define([], function() { return FormValidator; });
    } else if (typeof module === 'object' && module.exports) {
        module.exports = FormValidator;
    }

})(window, jQuery);