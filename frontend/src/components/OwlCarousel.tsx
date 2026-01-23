/**
 * Owl Carousel Wrapper - Exact jable.tv configuration
 */

import { useEffect, useRef, ReactNode } from 'react';
import 'owl.carousel/dist/assets/owl.carousel.css';
import $ from '@/lib/jquery-setup';

// Import owl carousel after jQuery is global
import 'owl.carousel';

// Extend jQuery to include owlCarousel
declare global {
    interface JQuery {
        owlCarousel(options?: any): JQuery;
    }
}

interface OwlCarouselProps {
    children: ReactNode;
    options?: any;
    className?: string;
}

export default function OwlCarousel({ 
    children, 
    options = {},
    className = ''
}: OwlCarouselProps) {
    const carouselRef = useRef<HTMLDivElement>(null);
    const isInitialized = useRef(false);

    useEffect(() => {
        if (!carouselRef.current) return;

        // Count children
        const childCount = Array.isArray(children) ? children.length : (children ? 1 : 0);
        console.log('OwlCarousel: Initializing with', childCount, 'items');

        // Wait for next tick to ensure DOM is ready
        const timer = setTimeout(() => {
            if (!carouselRef.current || isInitialized.current) return;

            const $carousel = $(carouselRef.current);
            
            // Initialize Owl Carousel - exact jable.tv settings
            try {
                $carousel.owlCarousel({
                    loop: false,
                    margin: 0,
                    nav: false,
                    dots: true,
                    autoplay: false,
                    autoHeight: false,
                    stagePadding: 0,
                    smartSpeed: 250,
                    fluidSpeed: true,
                    navSpeed: 250,
                    dotsSpeed: 250,
                    dragEndSpeed: 250,
                    responsive: {
                        0: {
                            items: 2
                        },
                        576: {
                            items: 3
                        },
                        992: {
                            items: 4
                        }
                    },
                    ...options
                });
                isInitialized.current = true;
                console.log('Owl Carousel initialized successfully with', childCount, 'items');
            } catch (error) {
                console.error('Owl Carousel initialization error:', error);
            }
        }, 100);

        // Cleanup
        return () => {
            clearTimeout(timer);
            if (isInitialized.current && carouselRef.current) {
                try {
                    $(carouselRef.current).trigger('destroy.owl.carousel');
                    isInitialized.current = false;
                } catch (error) {
                    console.error('Owl Carousel cleanup error:', error);
                }
            }
        };
    }, [options, children]);

    return (
        <div ref={carouselRef} className={`owl-carousel owl-theme-jable ${className}`}>
            {children}
        </div>
    );
}
