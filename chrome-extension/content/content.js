function getYouTubeVideoId() {
    const url = new URL(window.location.href);
    return url.searchParams.get('v');
}

function injectSidebar() {
    if (document.getElementById('vidora-sidebar')) return;
    
    const sidebar = document.createElement('iframe');
    sidebar.id = 'vidora-sidebar';
    sidebar.src = chrome.runtime.getURL('sidebar/sidebar.html');
    sidebar.style.position = 'fixed';
    sidebar.style.top = '0';
    sidebar.style.right = '0';
    sidebar.style.width = '420px';
    sidebar.style.height = '100%';
    sidebar.style.zIndex = '999999';
    sidebar.style.border = 'none';
    sidebar.style.boxShadow = '-4px 0 24px rgba(0,0,0,0.3)';
    sidebar.style.background = '#0a0a0a';
    sidebar.style.transition = 'transform 0.3s ease';
    
    document.body.appendChild(sidebar);
    
    sidebar.onload = () => {
        const videoId = getYouTubeVideoId();
        if (videoId) {
            sidebar.contentWindow.postMessage({ videoId }, '*');
        }
    };
}

function removeSidebar() {
    const sidebar = document.getElementById('vidora-sidebar');
    if (sidebar) sidebar.remove();
}

function injectSidebarButton() {
    const existingBtn = document.getElementById('vidora-sidebar-btn');
    if (existingBtn) existingBtn.remove();
    
    const btn = document.createElement('button');
    btn.id = 'vidora-sidebar-btn';
    btn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
    `;
    
    btn.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 999998;
        padding: 10px;
        background: rgba(20, 20, 20, 0.95);
        color: #6366F1;
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 10px;
        backdrop-filter: blur(10px);
        cursor: pointer;
        font-size: 13px;
        font-weight: 600;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    `;
    
    btn.onmouseover = () => {
        btn.style.background = 'rgba(99, 102, 241, 0.15)';
        btn.style.borderColor = '#6366F1';
        btn.style.transform = 'scale(1.05)';
        btn.style.boxShadow = '0 4px 12px rgba(99, 102, 241, 0.3)';
    };
    
    btn.onmouseout = () => {
        btn.style.background = 'rgba(20, 20, 20, 0.95)';
        btn.style.borderColor = 'rgba(99, 102, 241, 0.3)';
        btn.style.transform = 'scale(1)';
        btn.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.3)';
    };
    
    btn.onclick = () => {
        const sidebar = document.getElementById('vidora-sidebar');
        if (sidebar) {
            removeSidebar();
            btn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            `;
        } else {
            injectSidebar();
            btn.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z"/>
    </svg>
`;

        }
    };
    
    document.body.appendChild(btn);
}

// FIXED: Proper initialization with retry logic
function initializeButton() {
    const videoId = getYouTubeVideoId();
    if (!videoId) {
        setTimeout(initializeButton, 500);
        return;
    }
    
    injectSidebarButton();
}

// FIXED: Wait for YouTube's primary content to load
function waitForYouTube() {
    const ytdApp = document.querySelector('ytd-app');
    const ytdWatch = document.querySelector('ytd-watch-flexy');
    
    if (ytdApp && (ytdWatch || document.querySelector('#movie_player'))) {
        initializeButton();
    } else {
        setTimeout(waitForYouTube, 300);
    }
}

// Start initialization
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', waitForYouTube);
} else {
    waitForYouTube();
}

// Handle YouTube SPA navigation
let lastUrl = location.href;
const urlObserver = new MutationObserver(() => {
    const currentUrl = location.href;
    if (currentUrl !== lastUrl) {
        lastUrl = currentUrl;
        removeSidebar();
        setTimeout(waitForYouTube, 800);
    }
});

urlObserver.observe(document.querySelector('title'), {
    subtree: true,
    characterData: true,
    childList: true
});

// Listen for messages from background script
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    const iframe = document.getElementById('vidora-sidebar');
    if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage(msg, '*');
    }
});

// Listen for close sidebar message
window.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'CLOSE_SIDEBAR') {
        removeSidebar();
        const btn = document.getElementById('vidora-sidebar-btn');
        if (btn) {
            btn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            `;
        }
    }
});
