// Aggressive Ad Blocker Content Script
console.log('🛡️ AGGRESSIVE Ad Blocker Content Script Loaded');

// Comprehensive ad selectors
const adSelectors = [
    // Generic ad containers
    'iframe[src*="ad"]',
    'iframe[src*="banner"]',
    'iframe[src*="popup"]',
    'iframe[src*="doubleclick"]',
    'iframe[src*="googlesyndication"]',
    'iframe[src*="advertising"]',
    'iframe[src*="exoclick"]',
    'iframe[src*="popads"]',
    'iframe[src*="juicyads"]',
    'iframe[src*="trafficjunky"]',
    'iframe[src*="plugrush"]',
    
    // Javmix specific
    'iframe[src*="ad-nex"]',
    'iframe[src*="mavrtracktor"]',
    'iframe[src*="stripcash"]',
    'div[id*="di9o8snvoat"]',
    'script[id*="agmnb"]',
    'script[id*="ugmnb"]',
    'div[style*="stripcash"]',
    '.nx_mfbox',
    '[data-isboost-content]',
    
    // Generic patterns
    'div[class*="ad-"]',
    'div[id*="ad-"]',
    'div[class*="ad_"]',
    'div[id*="ad_"]',
    'div[class*="advertisement"]',
    'div[id*="advertisement"]',
    'div[class*="banner"]',
    'div[id*="banner"]',
    'div[class*="popup"]',
    'div[id*="popup"]',
    'div[class*="sponsor"]',
    'div[id*="sponsor"]',
    '.ad-container',
    '.ad-banner',
    '.ad-wrapper',
    '.ad-slot',
    '.ad-unit',
    '.ad-box',
    '.ad-frame',
    '.advertisement',
    '.adsbox',
    '.adsbygoogle',
    'ins.adsbygoogle',
    
    // Popups and overlays
    '.popup',
    '.modal-backdrop',
    '.overlay',
    '[class*="popup"]',
    '[id*="popup"]',
    '[class*="modal"]',
    '[id*="modal"]',
    '[class*="overlay"]',
    '[id*="overlay"]',
    
    // Scripts
    'script[src*="ad"]',
    'script[src*="doubleclick"]',
    'script[src*="googlesyndication"]',
    'script[src*="exoclick"]',
    'script[src*="popads"]',
    'script[src*="ad-nex"]'
];

// Nuclear option: Remove all iframes except video players
function removeAdIframes() {
    const iframes = document.querySelectorAll('iframe');
    let removed = 0;
    
    iframes.forEach(iframe => {
        const src = (iframe.src || '').toLowerCase();
        
        // Keep video player iframes
        const isVideoPlayer = 
            src.includes('streamtape') ||
            src.includes('doodstream') ||
            src.includes('pornhub') ||
            src.includes('likessb') ||
            src.includes('player') ||
            src.includes('video') ||
            src.includes('embed');
        
        // Remove if it's an ad
        if (!isVideoPlayer && (
            src.includes('ad') ||
            src.includes('banner') ||
            src.includes('popup') ||
            src.includes('mavrtracktor') ||
            src.includes('stripcash') ||
            src.includes('exoclick') ||
            src.includes('juicyads') ||
            src.includes('trafficjunky')
        )) {
            iframe.remove();
            removed++;
            console.log('🚫 Removed ad iframe:', src.substring(0, 50));
        }
    });
    
    return removed;
}

// Aggressive ad hiding
function hideAds() {
    let blockedCount = 0;
    
    // Method 1: CSS selectors
    adSelectors.forEach(selector => {
        try {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el && el.style.display !== 'none') {
                    // Nuclear removal
                    el.remove();
                    blockedCount++;
                }
            });
        } catch (e) {}
    });
    
    // Method 2: Remove ad iframes
    blockedCount += removeAdIframes();
    
    // Method 3: Remove elements with ad-related attributes
    try {
        const allElements = document.querySelectorAll('*');
        allElements.forEach(el => {
            const className = (el.className || '').toString().toLowerCase();
            const id = (el.id || '').toLowerCase();
            
            if (
                className.includes('ad-') ||
                className.includes('ad_') ||
                className.includes('advertisement') ||
                className.includes('banner') ||
                id.includes('ad-') ||
                id.includes('ad_') ||
                id.includes('advertisement') ||
                id.includes('banner')
            ) {
                el.remove();
                blockedCount++;
            }
        });
    } catch (e) {}
    
    if (blockedCount > 0) {
        console.log(`🚫 Blocked ${blockedCount} ad elements`);
    }
    
    return blockedCount;
}

// Block popup windows aggressively
function blockPopups() {
    // Override window.open completely
    window.open = function() {
        console.log('🚫 BLOCKED popup window');
        return null;
    };
    
    // Block all click events on suspicious links
    document.addEventListener('click', function(e) {
        const target = e.target.closest('a');
        if (target) {
            const href = (target.href || '').toLowerCase();
            if (
                target.target === '_blank' ||
                href.includes('ad') ||
                href.includes('popup') ||
                href.includes('click') ||
                href.includes('redirect') ||
                href.includes('track')
            ) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                console.log('🚫 BLOCKED suspicious link:', href.substring(0, 50));
                return false;
            }
        }
    }, true);
    
    // Block context menu on ads
    document.addEventListener('contextmenu', function(e) {
        const target = e.target;
        if (target.tagName === 'IFRAME' || target.closest('.ad-container')) {
            e.preventDefault();
            return false;
        }
    }, true);
}

// Inject aggressive CSS
function injectCSS() {
    const style = document.createElement('style');
    style.textContent = `
        /* Nuclear ad blocking */
        iframe[src*="ad"],
        iframe[src*="banner"],
        iframe[src*="popup"],
        iframe[src*="mavrtracktor"],
        iframe[src*="stripcash"],
        iframe[src*="exoclick"],
        iframe[src*="juicyads"],
        iframe[src*="ad-nex"],
        .ad-container, .ad-banner, .ad-wrapper, .ad-slot, .advertisement,
        .adsbox, .adsbygoogle, [class*="ad-"], [id*="ad-"],
        .nx_mfbox, [data-isboost-content],
        div[id*="di9o8snvoat"], script[id*="agmnb"], script[id*="ugmnb"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            height: 0 !important;
            width: 0 !important;
            position: absolute !important;
            left: -99999px !important;
            pointer-events: none !important;
        }
        
        /* Remove ad spaces */
        body {
            overflow-x: hidden !important;
        }
    `;
    (document.head || document.documentElement).appendChild(style);
    console.log('✅ Aggressive CSS injected');
}

// Initialize immediately
(function() {
    console.log('🛡️ Initializing aggressive ad blocker...');
    
    hideAds();
    blockPopups();
    injectCSS();
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            hideAds();
            console.log('✅ Ad blocker active on DOMContentLoaded');
        });
    }
    
    // Aggressive periodic checking
    let totalBlocked = 0;
    setInterval(function() {
        const blocked = hideAds();
        totalBlocked += blocked;
    }, 500);  // Check every 500ms
    
    // Observe ALL DOM changes
    const observer = new MutationObserver(function(mutations) {
        const blocked = hideAds();
        if (blocked > 0) {
            totalBlocked += blocked;
        }
    });
    
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['src', 'href', 'class', 'id']
    });
    
    // Report stats
    setInterval(function() {
        if (totalBlocked > 0) {
            console.log(`📊 Total ads blocked: ${totalBlocked}`);
        }
    }, 10000);
    
    console.log('✅ AGGRESSIVE ad blocker active and monitoring');
})();
