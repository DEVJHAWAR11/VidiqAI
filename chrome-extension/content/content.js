// chrome-extension/content/content.js

// Utility to get YouTube video ID from URL
function getYouTubeVideoId() {
  const url = new URL(window.location.href);
  return url.searchParams.get('v');
}

// Inject sidebar if not already present
function injectSidebar() {
  if (document.getElementById('vidiqai-sidebar')) return;

  // Create iframe for sidebar
  const sidebar = document.createElement('iframe');
  sidebar.id = 'vidiqai-sidebar';
  sidebar.src = chrome.runtime.getURL('sidebar/sidebar.html');
  sidebar.style.position = 'fixed';
  sidebar.style.top = '0';
  sidebar.style.right = '0';
  sidebar.style.width = '400px';
  sidebar.style.height = '100%';
  sidebar.style.zIndex = '999999';
  sidebar.style.border = 'none';
  sidebar.style.boxShadow = '0 0 16px rgba(0,0,0,0.2)';
  sidebar.style.background = '#fff';
  sidebar.style.transition = 'right 0.3s';

  document.body.appendChild(sidebar);
}

// Remove sidebar
function removeSidebar() {
  const sidebar = document.getElementById('vidiqai-sidebar');
  if (sidebar) sidebar.remove();
}

// Add a floating button to open/close sidebar
function injectSidebarButton() {
  if (document.getElementById('vidiqai-sidebar-btn')) return;

  const btn = document.createElement('button');
  btn.id = 'vidiqai-sidebar-btn';
  btn.innerText = '💬 Chat with Video';
  btn.style.position = 'fixed';
  btn.style.top = '80px';
  btn.style.right = '20px';
  btn.style.zIndex = '999999';
  btn.style.padding = '12px 18px';
  btn.style.background = '#6366f1';
  btn.style.color = '#fff';
  btn.style.border = 'none';
  btn.style.borderRadius = '8px';
  btn.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
  btn.style.cursor = 'pointer';
  btn.style.fontSize = '16px';

  btn.onclick = () => {
    const sidebar = document.getElementById('vidiqai-sidebar');
    if (sidebar) {
      removeSidebar();
    } else {
      injectSidebar();
    }
  };

  document.body.appendChild(btn);
}

// Listen for YouTube navigation (SPA)
let lastVideoId = null;
function checkForVideoChange() {
  const currentVideoId = getYouTubeVideoId();
  if (currentVideoId !== lastVideoId) {
    lastVideoId = currentVideoId;
    removeSidebar();
    injectSidebarButton();
  }
}

// Initial injection
injectSidebarButton();
checkForVideoChange();

// Observe URL changes (YouTube SPA navigation)
let lastUrl = location.href;
new MutationObserver(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    setTimeout(checkForVideoChange, 500);
  }
}).observe(document, {subtree: true, childList: true});
