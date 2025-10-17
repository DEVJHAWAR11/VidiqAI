// chrome-extension/background/background.js

// Configuration
const CONFIG = {
  API_BASE_URL: 'http://localhost:8000/api/v1',  // Change this when deployed
  API_TIMEOUT: 30000  // 30 seconds
};

// Listen for installation
chrome.runtime.onInstalled.addListener((details) => {
  console.log('✓ VidIQAI Extension Installed', details);
  
  // Set default settings
  chrome.storage.sync.set({
    apiUrl: CONFIG.API_BASE_URL,
    theme: 'light',
    autoProcess: true
  });
});

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📩 Background received message:', request.type);
  
  // Handle different message types
  switch(request.type) {
    case 'CHECK_TRANSCRIPT':
      checkTranscript(request.videoId)
        .then(sendResponse)
        .catch(err => sendResponse({ error: err.message }));
      return true;  // Keep channel open for async response
      
    case 'PROCESS_VIDEO':
      processVideo(request.videoId, request.videoUrl)
        .then(sendResponse)
        .catch(err => sendResponse({ error: err.message }));
      return true;
      
    case 'ASK_QUESTION':
      askQuestion(request.videoId, request.question)
        .then(sendResponse)
        .catch(err => sendResponse({ error: err.message }));
      return true;
      
    case 'GET_SUMMARY':
      getSummary(request.videoId)
        .then(sendResponse)
        .catch(err => sendResponse({ error: err.message }));
      return true;
  }
});

// API Functions
async function checkTranscript(videoId) {
  try {
    const settings = await chrome.storage.sync.get(['apiUrl']);
    const apiUrl = settings.apiUrl || CONFIG.API_BASE_URL;
    
    const response = await fetch(`${apiUrl}/check/${videoId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('✓ Transcript check:', data);
    return { success: true, data };
    
  } catch (error) {
    console.error('✗ Check transcript failed:', error);
    return { success: false, error: error.message };
  }
}

async function processVideo(videoId, videoUrl) {
  try {
    const settings = await chrome.storage.sync.get(['apiUrl']);
    const apiUrl = settings.apiUrl || CONFIG.API_BASE_URL;
    
    console.log(`🔄 Processing video: ${videoId}`);
    
    const response = await fetch(`${apiUrl}/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        video_url: videoUrl || `https://www.youtube.com/watch?v=${videoId}`
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('✓ Video processed:', data);
    return { success: true, data };
    
  } catch (error) {
    console.error('✗ Process video failed:', error);
    return { success: false, error: error.message };
  }
}

async function askQuestion(videoId, question) {
  try {
    const settings = await chrome.storage.sync.get(['apiUrl']);
    const apiUrl = settings.apiUrl || CONFIG.API_BASE_URL;
    
    console.log(`💬 Asking: "${question}"`);
    
    const response = await fetch(`${apiUrl}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        video_id: videoId,
        question: question
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('✓ Got answer:', data);
    return { success: true, data };
    
  } catch (error) {
    console.error('✗ Ask question failed:', error);
    return { success: false, error: error.message };
  }
}

async function getSummary(videoId) {
  try {
    const settings = await chrome.storage.sync.get(['apiUrl']);
    const apiUrl = settings.apiUrl || CONFIG.API_BASE_URL;
    
    console.log(`📝 Getting summary for: ${videoId}`);
    
    const response = await fetch(`${apiUrl}/summary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        video_id: videoId
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('✓ Got summary:', data);
    return { success: true, data };
    
  } catch (error) {
    console.error('✗ Get summary failed:', error);
    return { success: false, error: error.message };
  }
}

// Keep service worker alive
chrome.runtime.onConnect.addListener((port) => {
  console.log('🔌 Port connected:', port.name);
});

console.log('🚀 VidIQAI Background Service Worker Started');
