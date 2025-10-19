// chrome-extension/content/content.js

function getYouTubeVideoId() {
  const url = new URL(window.location.href);
  return url.searchParams.get('v');
}

function injectSidebar() {
  if (document.getElementById('vidiqai-sidebar')) return;

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

  sidebar.onload = () => {
    const videoId = getYouTubeVideoId();
    if (videoId) {
      sidebar.contentWindow.postMessage({ videoId }, '*');
    }
  };
}

function removeSidebar() {
  const sidebar = document.getElementById('vidiqai-sidebar');
  if (sidebar) sidebar.remove();
}

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
  btn.style.fontWeight = '600';
  btn.style.transition = 'all 0.2s';

  btn.onmouseover = () => {
    btn.style.background = '#4f46e5';
    btn.style.transform = 'translateY(-2px)';
    btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
  };
  btn.onmouseout = () => {
    btn.style.background = '#6366f1';
    btn.style.transform = 'translateY(0)';
    btn.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
  };

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

let lastVideoId = null;
function checkForVideoChange() {
  const currentVideoId = getYouTubeVideoId();
  if (currentVideoId !== lastVideoId) {
    lastVideoId = currentVideoId;
    removeSidebar();
    injectSidebarButton();
  }
}

injectSidebarButton();
checkForVideoChange();

let lastUrl = location.href;
new MutationObserver(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    setTimeout(checkForVideoChange, 500);
  }
}).observe(document, {subtree: true, childList: true});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  const iframe = document.getElementById('vidiqai-sidebar');
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.postMessage(msg, '*');
  }
});

window.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'CLOSE_SIDEBAR') {
    removeSidebar();
  }
});

window.addEventListener('message', (event) => {
  if (event.data?.type === 'CLOSE_SIDEBAR') {
    removeSidebar();
  }
});
