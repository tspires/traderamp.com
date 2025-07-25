/**
 * TradeRamp Application JavaScript - Clean Code Version
 * @module TradeRampApp
 * @description Main application module following clean code principles
 */

(function(window, document, $) {
    'use strict';

    // Configuration Constants
    const CONFIG = {
        // Animation and timing
        ANIMATION: {
            DURATION: 1000,
            FADE_DURATION: 1000,
            ISOTOPE_DURATION: 750
        },
        
        // Scroll offsets
        SCROLL: {
            OFFSET: 100,
            AFFIX_OFFSET: 50,
            PROGRESS_BAR_OFFSET: 50
        },
        
        // Responsive breakpoints
        BREAKPOINTS: {
            MOBILE: 0,
            TABLET: 600,
            DESKTOP: 1000
        },
        
        // API endpoints
        ENDPOINTS: {
            MAILCHIMP: '', // Set from data attribute
            CAMPAIGN_MONITOR: '' // Set from form action
        },
        
        // Messages
        MESSAGES: {
            CAMPAIGN_MONITOR: {
                SUCCESS: 'Success: ',
                ERROR: 'Error: '
            }
        },
        
        // Selectors
        SELECTORS: {
            // Background
            BG_SECTION: '.bg-section',
            BG_PATTERN: '.bg-pattern',
            COL_BG: '.col-bg',
            
            // Navigation
            DROPDOWN_TOGGLE: 'ul.dropdown-menu [data-toggle=dropdown]',
            NAV_AFFIX: '.header-fixed .navbar-fixed-top',
            SCROLL_LINK: 'a[data-scroll="scrollTo"]',
            NAV_SPLIT: '.nav-split',
            BODY_SCROLL: '.body-scroll',
            
            // Carousel
            CAROUSEL: '.carousel',
            
            // Popup
            IMG_POPUP: '.img-popup',
            IMG_GALLERY: '.img-gallery-item',
            VIDEO_POPUP: '.popup-video,.popup-gmaps',
            
            // Portfolio
            PORTFOLIO_FILTER: '.portfolio-filter',
            PORTFOLIO_ALL: '#portfolio-all',
            PORTFOLIO_ITEM: '.portfolio-item',
            
            // Progress
            SKILLS: '.skills',
            SKILLS_SCROLL: '.skills-scroll',
            PROGRESS_BAR: '.progress-bar',
            
            // Forms
            MAILCHIMP: '.mailchimp',
            CAMPAIGN_MONITOR: '#campaignmonitor',
            COUNTDOWN: '.countdown',
            SUBSCRIBE_ALERT: '.subscribe-alert',
            
            // Map
            GOOGLE_MAP: '.googleMap'
        }
    };

    /**
     * Background Image Module
     * @namespace BackgroundModule
     */
    const BackgroundModule = {
        /**
         * Initialize all background image processing
         * @public
         */
        init() {
            this.processBackgrounds(CONFIG.SELECTORS.BG_SECTION);
            this.processBackgrounds(CONFIG.SELECTORS.BG_PATTERN);
            this.processBackgrounds(CONFIG.SELECTORS.COL_BG);
        },

        /**
         * Process background images for given selector
         * @param {string} selector - CSS selector for elements
         * @private
         */
        processBackgrounds(selector) {
            $(selector).each((index, element) => {
                this.setBackgroundImage($(element));
            });
        },

        /**
         * Set background image from child img element
         * @param {jQuery} $element - jQuery element to process
         * @private
         */
        setBackgroundImage($element) {
            const $img = $element.children('img');
            const imgSrc = $img.attr('src');
            
            if (!imgSrc) return;
            
            const className = $element.attr('class').split(' ')[0];
            $element.parent()
                .css('backgroundImage', `url(${imgSrc})`)
                .addClass(className);
            $element.remove();
        }
    };

    /**
     * Navigation Module
     * @namespace NavigationModule
     */
    const NavigationModule = {
        /**
         * Initialize all navigation features
         * @public
         */
        init() {
            this.initMobileMenu();
            this.initHeaderAffix();
            this.initSmoothScroll();
            this.initScrollSpy();
        },

        /**
         * Initialize mobile dropdown menu
         * @private
         */
        initMobileMenu() {
            $(CONFIG.SELECTORS.DROPDOWN_TOGGLE).on('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                
                const $toggle = $(event.currentTarget);
                $toggle.parent().siblings().removeClass('open');
                $toggle.parent().toggleClass('open');
            });
        },

        /**
         * Initialize fixed header on scroll
         * @private
         */
        initHeaderAffix() {
            const $navAffix = $(CONFIG.SELECTORS.NAV_AFFIX);
            
            if (!$navAffix.length) return;
            
            $navAffix.affix({
                offset: {
                    top: CONFIG.SCROLL.AFFIX_OFFSET
                }
            });
        },

        /**
         * Initialize smooth scrolling for anchor links
         * @private
         */
        initSmoothScroll() {
            $(CONFIG.SELECTORS.SCROLL_LINK).on('click', (event) => {
                const href = $(event.currentTarget).attr('href');
                const $target = $(href);
                
                if (!$target.length) return;
                
                event.preventDefault();
                this.scrollToElement($target, $(event.currentTarget));
            });
        },

        /**
         * Scroll to target element with animation
         * @param {jQuery} $target - Target element
         * @param {jQuery} $link - Clicked link element
         * @private
         */
        scrollToElement($target, $link) {
            const scrollTop = $target.offset().top - CONFIG.SCROLL.OFFSET;
            
            $('html, body').animate(
                { scrollTop },
                CONFIG.ANIMATION.DURATION
            );
            
            if ($link.hasClass('menu-item')) {
                $link.parent()
                    .addClass('active')
                    .siblings()
                    .removeClass('active');
            }
        },

        /**
         * Initialize scroll spy for navigation
         * @private
         */
        initScrollSpy() {
            if (!$(CONFIG.SELECTORS.BODY_SCROLL).length) return;
            
            $(window).on('scroll', () => {
                this.updateActiveNavItem();
            });
        },

        /**
         * Update active navigation item based on scroll position
         * @private
         */
        updateActiveNavItem() {
            const scrollPosition = $(window).scrollTop();
            
            $('.section').each((index, element) => {
                const $section = $(element);
                const sectionID = $section.attr('id');
                
                if (!sectionID) return;
                
                const sectionTop = $section.offset().top - CONFIG.SCROLL.OFFSET;
                const sectionHeight = $section.outerHeight();
                
                if (this.isInViewport(scrollPosition, sectionTop, sectionHeight)) {
                    this.setActiveNavItem(sectionID);
                }
            });
        },

        /**
         * Check if section is in viewport
         * @param {number} scrollPosition - Current scroll position
         * @param {number} sectionTop - Section top position
         * @param {number} sectionHeight - Section height
         * @returns {boolean}
         * @private
         */
        isInViewport(scrollPosition, sectionTop, sectionHeight) {
            return scrollPosition > sectionTop - 1 && 
                   scrollPosition < sectionTop + sectionHeight - 1;
        },

        /**
         * Set active navigation item
         * @param {string} sectionID - Section ID
         * @private
         */
        setActiveNavItem(sectionID) {
            const $navItem = $(`.nav-split a[href='#${sectionID}']`).parent();
            $navItem.addClass('active').siblings().removeClass('active');
        }
    };

    /**
     * Carousel Module
     * @namespace CarouselModule
     */
    const CarouselModule = {
        /**
         * Initialize all carousels
         * @public
         */
        init() {
            $(CONFIG.SELECTORS.CAROUSEL).each((index, element) => {
                this.initCarousel($(element));
            });
        },

        /**
         * Initialize individual carousel
         * @param {jQuery} $carousel - Carousel element
         * @private
         */
        initCarousel($carousel) {
            const options = this.getCarouselOptions($carousel);
            $carousel.owlCarousel(options);
        },

        /**
         * Get carousel options from data attributes
         * @param {jQuery} $carousel - Carousel element
         * @returns {Object} Carousel options
         * @private
         */
        getCarouselOptions($carousel) {
            return {
                loop: $carousel.data('loop'),
                autoplay: $carousel.data('autoplay'),
                margin: $carousel.data('space'),
                nav: $carousel.data('nav'),
                dots: $carousel.data('dots'),
                center: $carousel.data('center'),
                dotsSpeed: $carousel.data('speed'),
                responsive: this.getResponsiveOptions($carousel)
            };
        },

        /**
         * Get responsive options for carousel
         * @param {jQuery} $carousel - Carousel element
         * @returns {Object} Responsive configuration
         * @private
         */
        getResponsiveOptions($carousel) {
            return {
                [CONFIG.BREAKPOINTS.MOBILE]: { items: 1 },
                [CONFIG.BREAKPOINTS.TABLET]: { items: $carousel.data('slide-rs') },
                [CONFIG.BREAKPOINTS.DESKTOP]: { items: $carousel.data('slide') }
            };
        }
    };

    /**
     * Popup Module
     * @namespace PopupModule
     */
    const PopupModule = {
        /**
         * Initialize all popup types
         * @public
         */
        init() {
            this.initImagePopups();
            this.initVideoPopups();
        },

        /**
         * Initialize image popups
         * @private
         */
        initImagePopups() {
            $(CONFIG.SELECTORS.IMG_POPUP).magnificPopup({
                type: 'image'
            });
            
            $(CONFIG.SELECTORS.IMG_GALLERY).magnificPopup({
                type: 'image',
                gallery: { enabled: true }
            });
        },

        /**
         * Initialize video popups
         * @private
         */
        initVideoPopups() {
            $(CONFIG.SELECTORS.VIDEO_POPUP).magnificPopup({
                disableOn: 700,
                mainClass: 'mfp-fade',
                removalDelay: 0,
                preloader: false,
                fixedContentPos: false,
                type: 'iframe',
                iframe: this.getIframeOptions()
            });
        },

        /**
         * Get iframe options for video popups
         * @returns {Object} Iframe configuration
         * @private
         */
        getIframeOptions() {
            return {
                markup: this.getIframeMarkup(),
                patterns: {
                    youtube: {
                        index: 'youtube.com/',
                        id: 'v=',
                        src: '//www.youtube.com/embed/%id%?autoplay=1'
                    }
                },
                srcAction: 'iframe_src'
            };
        },

        /**
         * Get iframe markup template
         * @returns {string} HTML markup
         * @private
         */
        getIframeMarkup() {
            return '<div class="mfp-iframe-scaler">' +
                   '<div class="mfp-close"></div>' +
                   '<iframe class="mfp-iframe" frameborder="0" allowfullscreen></iframe>' +
                   '</div>';
        }
    };

    /**
     * Portfolio Module
     * @namespace PortfolioModule
     */
    const PortfolioModule = {
        /**
         * Initialize portfolio filtering
         * @public
         */
        init() {
            const $portfolioFilter = $(CONFIG.SELECTORS.PORTFOLIO_FILTER);
            
            if (!$portfolioFilter.length) return;
            
            this.initIsotope();
            this.bindFilterEvents($portfolioFilter);
        },

        /**
         * Initialize Isotope plugin
         * @private
         */
        initIsotope() {
            const $portfolioAll = $(CONFIG.SELECTORS.PORTFOLIO_ALL);
            
            $portfolioAll.imagesLoaded().progress(() => {
                $portfolioAll.isotope(this.getIsotopeOptions('*'));
            });
        },

        /**
         * Bind filter click events
         * @param {jQuery} $portfolioFilter - Filter container
         * @private
         */
        bindFilterEvents($portfolioFilter) {
            $portfolioFilter.find('a').on('click', (event) => {
                event.preventDefault();
                this.handleFilterClick($(event.currentTarget), $portfolioFilter);
            });
        },

        /**
         * Handle filter click
         * @param {jQuery} $filter - Clicked filter
         * @param {jQuery} $portfolioFilter - Filter container
         * @private
         */
        handleFilterClick($filter, $portfolioFilter) {
            const filterValue = $filter.attr('data-filter');
            
            // Update active state
            $portfolioFilter.find('a.active-filter').removeClass('active-filter');
            $filter.addClass('active-filter');
            
            // Apply filter
            this.applyFilter(filterValue);
        },

        /**
         * Apply portfolio filter
         * @param {string} filterValue - Filter selector
         * @private
         */
        applyFilter(filterValue) {
            const $portfolioAll = $(CONFIG.SELECTORS.PORTFOLIO_ALL);
            
            $portfolioAll.imagesLoaded().progress(() => {
                $portfolioAll.isotope(this.getIsotopeOptions(filterValue));
            });
        },

        /**
         * Get Isotope options
         * @param {string} filter - Filter selector
         * @returns {Object} Isotope configuration
         * @private
         */
        getIsotopeOptions(filter) {
            return {
                filter: filter,
                animationOptions: {
                    duration: CONFIG.ANIMATION.ISOTOPE_DURATION,
                    itemSelector: CONFIG.SELECTORS.PORTFOLIO_ITEM,
                    easing: 'linear',
                    queue: false
                }
            };
        }
    };

    /**
     * Progress Bar Module
     * @namespace ProgressBarModule
     */
    const ProgressBarModule = {
        /**
         * Initialize progress bars
         * @public
         */
        init() {
            if ($(CONFIG.SELECTORS.SKILLS).length) {
                this.initScrollProgress();
            }
            
            if ($(CONFIG.SELECTORS.SKILLS_SCROLL).length) {
                this.animateProgressBars();
            }
        },

        /**
         * Initialize scroll-triggered progress bars
         * @private
         */
        initScrollProgress() {
            $(window).on('scroll', () => {
                const $skills = $(CONFIG.SELECTORS.SKILLS);
                const skillsTop = $skills.offset().top - CONFIG.SCROLL.PROGRESS_BAR_OFFSET;
                const skillsHeight = $skills.outerHeight();
                const scrollPosition = $(window).scrollTop();
                
                if (this.isInViewport(scrollPosition, skillsTop, skillsHeight)) {
                    this.animateProgressBars();
                }
            });
        },

        /**
         * Check if element is in viewport
         * @param {number} scrollPosition - Current scroll position
         * @param {number} elementTop - Element top position
         * @param {number} elementHeight - Element height
         * @returns {boolean}
         * @private
         */
        isInViewport(scrollPosition, elementTop, elementHeight) {
            return scrollPosition > elementTop - 1 && 
                   scrollPosition < elementTop + elementHeight - 1;
        },

        /**
         * Animate all progress bars
         * @private
         */
        animateProgressBars() {
            $(CONFIG.SELECTORS.PROGRESS_BAR).each((index, element) => {
                const $bar = $(element);
                const value = $bar.attr('aria-valuenow');
                $bar.width(`${value}%`);
            });
        }
    };

    /**
     * Forms Module
     * @namespace FormsModule
     */
    const FormsModule = {
        /**
         * Initialize all form handlers
         * @public
         */
        init() {
            this.initMailchimp();
            this.initCampaignMonitor();
            this.initCountdown();
        },

        /**
         * Initialize Mailchimp form
         * @private
         */
        initMailchimp() {
            const $mailchimp = $(CONFIG.SELECTORS.MAILCHIMP);
            
            if (!$mailchimp.length) return;
            
            $mailchimp.ajaxChimp({
                url: $mailchimp.data('url') || CONFIG.ENDPOINTS.MAILCHIMP,
                callback: (response) => this.handleMailchimpResponse(response)
            });
        },

        /**
         * Handle Mailchimp response
         * @param {Object} response - Mailchimp response
         * @private
         */
        handleMailchimpResponse(response) {
            const alertClass = response.result === 'success' ? 'alert-success' : 'alert-danger';
            const $alert = $(CONFIG.SELECTORS.SUBSCRIBE_ALERT);
            
            $alert.html(`<div class="alert ${alertClass}">${response.msg}</div>`)
                  .fadeIn(CONFIG.ANIMATION.FADE_DURATION);
        },

        /**
         * Initialize Campaign Monitor form
         * @private
         */
        initCampaignMonitor() {
            $(CONFIG.SELECTORS.CAMPAIGN_MONITOR).on('submit', (event) => {
                event.preventDefault();
                this.submitCampaignMonitor($(event.currentTarget));
            });
        },

        /**
         * Submit Campaign Monitor form
         * @param {jQuery} $form - Form element
         * @private
         */
        submitCampaignMonitor($form) {
            const url = `${$form.attr('action')}?callback=?`;
            const data = $form.serialize();
            
            $.getJSON(url, data)
                .done((response) => this.handleCampaignMonitorResponse(response))
                .fail(() => this.handleCampaignMonitorError());
        },

        /**
         * Handle Campaign Monitor response
         * @param {Object} data - Response data
         * @private
         */
        handleCampaignMonitorResponse(data) {
            const isError = data.Status === 400;
            const prefix = isError ? CONFIG.MESSAGES.CAMPAIGN_MONITOR.ERROR : CONFIG.MESSAGES.CAMPAIGN_MONITOR.SUCCESS;
            const message = prefix + data.Message;
            
            // Replace alert with proper UI notification
            this.showNotification(message, isError ? 'danger' : 'success');
        },

        /**
         * Handle Campaign Monitor error
         * @private
         */
        handleCampaignMonitorError() {
            this.showNotification('An error occurred. Please try again.', 'danger');
        },

        /**
         * Show notification message
         * @param {string} message - Message to display
         * @param {string} type - Message type (success/danger)
         * @private
         */
        showNotification(message, type) {
            // Implementation depends on notification system
            // For now, using console as placeholder
            if (type === 'danger') {
                console.error(message);
            } else {
                console.info(message);
            }
        },

        /**
         * Initialize countdown timers
         * @private
         */
        initCountdown() {
            $(CONFIG.SELECTORS.COUNTDOWN).each((index, element) => {
                this.initSingleCountdown($(element));
            });
        },

        /**
         * Initialize single countdown
         * @param {jQuery} $countdown - Countdown element
         * @private
         */
        initSingleCountdown($countdown) {
            const countDate = $countdown.data('count-date');
            
            if (!countDate) return;
            
            const targetDate = new Date(countDate);
            
            $countdown.countdown({
                until: targetDate,
                format: 'MMMM Do , h:mm:ss a'
            });
        }
    };

    /**
     * Map Module
     * @namespace MapModule
     */
    const MapModule = {
        /**
         * Initialize Google Maps
         * @public
         */
        init() {
            $(CONFIG.SELECTORS.GOOGLE_MAP).each((index, element) => {
                this.initMap($(element));
            });
        },

        /**
         * Initialize individual map
         * @param {jQuery} $map - Map element
         * @private
         */
        initMap($map) {
            const options = this.getMapOptions($map);
            
            if (!options.address) return;
            
            $map.gMap(options);
        },

        /**
         * Get map options from data attributes
         * @param {jQuery} $map - Map element
         * @returns {Object} Map configuration
         * @private
         */
        getMapOptions($map) {
            return {
                address: $map.data('map-address'),
                zoom: $map.data('map-zoom'),
                maptype: $map.data('map-type'),
                markers: [{
                    address: $map.data('map-address'),
                    maptype: $map.data('map-type'),
                    html: $map.data('map-info'),
                    icon: {
                        image: "assets/images/gmap/maker.png",
                        iconsize: [41, 54],
                        iconanchor: [41, 54]
                    }
                }]
            };
        }
    };

    /**
     * Main Application Controller
     * @namespace TradeRampApp
     */
    const TradeRampApp = {
        /**
         * Initialize the entire application
         * @public
         */
        init() {
            try {
                BackgroundModule.init();
                NavigationModule.init();
                CarouselModule.init();
                PopupModule.init();
                PortfolioModule.init();
                ProgressBarModule.init();
                FormsModule.init();
                MapModule.init();
            } catch (error) {
                console.error('Application initialization error:', error);
            }
        },

        /**
         * Get module reference
         * @param {string} moduleName - Name of module
         * @returns {Object} Module reference
         * @public
         */
        getModule(moduleName) {
            const modules = {
                background: BackgroundModule,
                navigation: NavigationModule,
                carousel: CarouselModule,
                popup: PopupModule,
                portfolio: PortfolioModule,
                progressBar: ProgressBarModule,
                forms: FormsModule,
                map: MapModule
            };
            
            return modules[moduleName];
        }
    };

    // Initialize when DOM is ready
    $(document).ready(() => {
        TradeRampApp.init();
    });

    // Expose to global scope for debugging/testing
    window.TradeRampApp = TradeRampApp;

})(window, document, jQuery);