/**
 * TradeRamp Application JavaScript
 * Organized using module pattern for better separation of concerns
 */

(function(window, document, $) {
    'use strict';

    // Constants
    const CONFIG = {
        SCROLL_OFFSET: 100,
        AFFIX_OFFSET: 50,
        PROGRESS_BAR_OFFSET: 50,
        ANIMATION_DURATION: 1000,
        CAROUSEL_BREAKPOINTS: {
            MOBILE: 0,
            TABLET: 600,
            DESKTOP: 1000
        }
    };

    // Background Module
    const BackgroundModule = {
        selectors: {
            bgSection: '.bg-section',
            bgPattern: '.bg-pattern',
            colBg: '.col-bg'
        },

        init() {
            this.processBackgrounds(this.selectors.bgSection);
            this.processBackgrounds(this.selectors.bgPattern);
            this.processBackgrounds(this.selectors.colBg);
        },

        processBackgrounds(selector) {
            $(selector).each(function() {
                const $element = $(this);
                const imgSrc = $element.children('img').attr('src');
                
                if (imgSrc) {
                    const bgUrl = `url(${imgSrc})`;
                    $element.parent()
                        .css('backgroundImage', bgUrl)
                        .addClass(selector.substring(1)); // Remove the dot
                    $element.remove();
                }
            });
        }
    };

    // Navigation Module
    const NavigationModule = {
        init() {
            this.initMobileMenu();
            this.initHeaderAffix();
            this.initSmoothScroll();
            this.initNavSplit();
        },

        initMobileMenu() {
            const $dropToggle = $('ul.dropdown-menu [data-toggle=dropdown]');
            
            $dropToggle.on('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                
                const $this = $(this);
                $this.parent().siblings().removeClass('open');
                $this.parent().toggleClass('open');
            });
        },

        initHeaderAffix() {
            const $navAffix = $('.header-fixed .navbar-fixed-top');
            
            if ($navAffix.length) {
                $navAffix.affix({
                    offset: {
                        top: CONFIG.AFFIX_OFFSET
                    }
                });
            }
        },

        initSmoothScroll() {
            const $scrollLinks = $('a[data-scroll="scrollTo"]');
            
            $scrollLinks.on('click', function(event) {
                const $target = $($(this).attr('href'));
                
                if ($target.length) {
                    event.preventDefault();
                    
                    $('html, body').animate({
                        scrollTop: $target.offset().top - CONFIG.SCROLL_OFFSET
                    }, CONFIG.ANIMATION_DURATION);
                    
                    // Update active menu item
                    if ($(this).hasClass('menu-item')) {
                        $(this).parent()
                            .addClass('active')
                            .siblings()
                            .removeClass('active');
                    }
                }
            });
        },

        initNavSplit() {
            if (!$('.body-scroll').length) return;
            
            $(window).on('scroll', function() {
                $('.section').each(function() {
                    const $section = $(this);
                    const sectionID = $section.attr('id');
                    const sectionTop = $section.offset().top - CONFIG.SCROLL_OFFSET;
                    const sectionHeight = $section.outerHeight();
                    const scrollPosition = $(window).scrollTop();
                    
                    if (scrollPosition > sectionTop - 1 && 
                        scrollPosition < sectionTop + sectionHeight - 1) {
                        const $navItem = $(`.nav-split a[href='#${sectionID}']`).parent();
                        $navItem.addClass('active').siblings().removeClass('active');
                    }
                });
            });
        }
    };

    // Carousel Module
    const CarouselModule = {
        init() {
            $('.carousel').each(function() {
                const $carousel = $(this);
                const options = {
                    loop: $carousel.data('loop'),
                    autoplay: $carousel.data('autoplay'),
                    margin: $carousel.data('space'),
                    nav: $carousel.data('nav'),
                    dots: $carousel.data('dots'),
                    center: $carousel.data('center'),
                    dotsSpeed: $carousel.data('speed'),
                    responsive: {
                        [CONFIG.CAROUSEL_BREAKPOINTS.MOBILE]: {
                            items: 1
                        },
                        [CONFIG.CAROUSEL_BREAKPOINTS.TABLET]: {
                            items: $carousel.data('slide-rs')
                        },
                        [CONFIG.CAROUSEL_BREAKPOINTS.DESKTOP]: {
                            items: $carousel.data('slide')
                        }
                    }
                };
                
                $carousel.owlCarousel(options);
            });
        }
    };

    // Popup Module
    const PopupModule = {
        init() {
            this.initImagePopups();
            this.initVideoPopups();
        },

        initImagePopups() {
            $('.img-popup').magnificPopup({
                type: 'image'
            });
            
            $('.img-gallery-item').magnificPopup({
                type: 'image',
                gallery: {
                    enabled: true
                }
            });
        },

        initVideoPopups() {
            $('.popup-video, .popup-gmaps').magnificPopup({
                disableOn: 700,
                mainClass: 'mfp-fade',
                removalDelay: 0,
                preloader: false,
                fixedContentPos: false,
                type: 'iframe',
                iframe: {
                    markup: '<div class="mfp-iframe-scaler">' +
                            '<div class="mfp-close"></div>' +
                            '<iframe class="mfp-iframe" frameborder="0" allowfullscreen></iframe>' +
                            '</div>',
                    patterns: {
                        youtube: {
                            index: 'youtube.com/',
                            id: 'v=',
                            src: '//www.youtube.com/embed/%id%?autoplay=1'
                        }
                    },
                    srcAction: 'iframe_src'
                }
            });
        }
    };

    // Portfolio Module
    const PortfolioModule = {
        init() {
            const $portfolioFilter = $('.portfolio-filter');
            const $portfolioAll = $('#portfolio-all');
            
            if (!$portfolioFilter.length) return;
            
            // Initialize Isotope
            $portfolioAll.imagesLoaded().progress(() => {
                $portfolioAll.isotope({
                    filter: '*',
                    animationOptions: {
                        duration: 750,
                        itemSelector: '.portfolio-item',
                        easing: 'linear',
                        queue: false
                    }
                });
            });
            
            // Filter click handler
            $portfolioFilter.find('a').on('click', function(e) {
                e.preventDefault();
                
                const $this = $(this);
                const filterValue = $this.attr('data-filter');
                
                // Update active state
                $portfolioFilter.find('a.active-filter').removeClass('active-filter');
                $this.addClass('active-filter');
                
                // Apply filter
                $portfolioAll.imagesLoaded().progress(() => {
                    $portfolioAll.isotope({
                        filter: filterValue,
                        animationOptions: {
                            duration: 750,
                            itemSelector: '.portfolio-item',
                            easing: 'linear',
                            queue: false
                        }
                    });
                });
            });
        }
    };

    // Progress Bar Module
    const ProgressBarModule = {
        init() {
            if ($('.skills').length) {
                this.initScrollProgress();
            }
            
            if ($('.skills-scroll').length) {
                this.initImmediateProgress();
            }
        },

        initScrollProgress() {
            $(window).on('scroll', () => {
                const $skills = $('.skills');
                const skillsTop = $skills.offset().top - CONFIG.PROGRESS_BAR_OFFSET;
                const skillsHeight = $skills.outerHeight();
                const scrollPosition = $(window).scrollTop();
                
                if (scrollPosition > skillsTop - 1 && 
                    scrollPosition < skillsTop + skillsHeight - 1) {
                    this.animateProgressBars();
                }
            });
        },

        initImmediateProgress() {
            this.animateProgressBars();
        },

        animateProgressBars() {
            $('.progress-bar').each(function() {
                const $bar = $(this);
                const value = $bar.attr('aria-valuenow');
                $bar.width(`${value}%`);
            });
        }
    };

    // Forms Module
    const FormsModule = {
        init() {
            this.initMailchimp();
            this.initCampaignMonitor();
            this.initCountdown();
        },

        initMailchimp() {
            const $mailchimp = $('.mailchimp');
            if (!$mailchimp.length) return;
            
            $mailchimp.ajaxChimp({
                url: $mailchimp.data('url') || '', // Get URL from data attribute
                callback: this.mailchimpCallback
            });
        },

        mailchimpCallback(resp) {
            const $alert = $('.subscribe-alert');
            const alertClass = resp.result === 'success' ? 'alert-success' : 'alert-danger';
            
            $alert.html(`<div class="alert ${alertClass}">${resp.msg}</div>`)
                  .fadeIn(1000);
        },

        initCampaignMonitor() {
            $('#campaignmonitor').on('submit', function(e) {
                e.preventDefault();
                
                $.getJSON(
                    `${this.action}?callback=?`,
                    $(this).serialize(),
                    (data) => {
                        const message = data.Status === 400 
                            ? `Error: ${data.Message}`
                            : `Success: ${data.Message}`;
                        alert(message);
                    }
                );
            });
        },

        initCountdown() {
            $('.countdown').each(function() {
                const $countdown = $(this);
                const countDate = $countdown.data('count-date');
                const targetDate = new Date(countDate);
                
                $countdown.countdown({
                    until: targetDate,
                    format: 'MMMM Do , h:mm:ss a'
                });
            });
        }
    };

    // Main App
    const TradeRampApp = {
        init() {
            // Initialize all modules
            BackgroundModule.init();
            NavigationModule.init();
            CarouselModule.init();
            PopupModule.init();
            PortfolioModule.init();
            ProgressBarModule.init();
            FormsModule.init();
        }
    };

    // Initialize when DOM is ready
    $(document).ready(() => {
        TradeRampApp.init();
    });

    // Expose to global scope if needed
    window.TradeRampApp = TradeRampApp;

})(window, document, jQuery);