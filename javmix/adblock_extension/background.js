// Aggressive Ad Blocker Background Script (Manifest V2)
console.log('🛡️ Aggressive Ad Blocker Loaded');

// Comprehensive list of ad domains
const adDomains = [
    // Google Ads
    '*://*.doubleclick.net/*',
    '*://*.googlesyndication.com/*',
    '*://*.googleadservices.com/*',
    '*://pagead2.googlesyndication.com/*',
    '*://*.googletagservices.com/*',
    '*://adservice.google.com/*',
    
    // Adult site ads
    '*://*.exoclick.com/*',
    '*://*.popads.net/*',
    '*://*.popcash.net/*',
    '*://*.juicyads.com/*',
    '*://*.trafficjunky.net/*',
    '*://*.trafficjunky.com/*',
    '*://*.adxpansion.com/*',
    '*://*.plugrush.com/*',
    '*://*.adsco.re/*',
    '*://*.adtng.com/*',
    '*://*.tsyndicate.com/*',
    '*://*.contentabc.com/*',
    '*://*.adnium.com/*',
    
    // Specific to javmix
    '*://ad-nex.com/*',
    '*://img.ad-nex.com/*',
    '*://creative.mavrtracktor.com/*',
    '*://*.stripcash.com/*',
    '*://*.mavrtracktor.com/*',
    
    // General ad networks
    '*://*.advertising.com/*',
    '*://*.adnxs.com/*',
    '*://*.adsrvr.org/*',
    '*://*.google-analytics.com/*',
    '*://*.scorecardresearch.com/*',
    '*://*.zedo.com/*',
    '*://*.fastclick.net/*',
    '*://*.admob.com/*',
    '*://*.outbrain.com/*',
    '*://*.taboola.com/*',
    '*://*.adroll.com/*',
    '*://*.criteo.com/*',
    '*://*.advertising.com/*',
    '*://*.2mdn.net/*',
    '*://*.adform.net/*',
    '*://*.serving-sys.com/*',
    
    // Tracking
    '*://*.hotjar.com/*',
    '*://*.mouseflow.com/*',
    '*://*.crazyegg.com/*',
    '*://*.luckyorange.com/*'
];

// Block ad requests
chrome.webRequest.onBeforeRequest.addListener(
    function(details) {
        console.log('🚫 BLOCKED:', details.url.substring(0, 100));
        return {cancel: true};
    },
    {urls: adDomains},
    ["blocking"]
);

// Also block by URL patterns
chrome.webRequest.onBeforeRequest.addListener(
    function(details) {
        const url = details.url.toLowerCase();
        
        // Block URLs containing these keywords
        const blockKeywords = [
            '/ads/',
            '/ad/',
            '/adv/',
            '/banner/',
            '/popup/',
            '/popunder/',
            'advertisement',
            'adserver',
            'adservice',
            'adsystem',
            '/track/',
            '/tracking/',
            '/analytics/',
            '/beacon/',
            'ad-nex',
            'mavrtracktor',
            'stripcash'
        ];
        
        for (const keyword of blockKeywords) {
            if (url.includes(keyword)) {
                console.log('🚫 BLOCKED (keyword):', details.url.substring(0, 100));
                return {cancel: true};
            }
        }
        
        return {cancel: false};
    },
    {urls: ["<all_urls>"]},
    ["blocking"]
);

// Block popup windows
chrome.windows.onCreated.addListener(function(window) {
    if (window.type === 'popup') {
        console.log('🚫 Blocked popup window');
        chrome.windows.remove(window.id);
    }
});

// Block new tabs that look like ads
chrome.tabs.onCreated.addListener(function(tab) {
    if (tab.url && (
        tab.url.includes('ad') || 
        tab.url.includes('popup') ||
        tab.url.includes('click') ||
        tab.url.includes('redirect')
    )) {
        console.log('🚫 Blocked ad tab:', tab.url);
        chrome.tabs.remove(tab.id);
    }
});

console.log('✅ Aggressive ad blocker active - blocking', adDomains.length, 'domains + keyword filtering');
