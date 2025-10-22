// Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api/v1',
    API_TIMEOUT: 30000
};

// Installation handler
chrome.runtime.onInstalled.addListener((details) => {
    console.log('✓ Vidora Extension Installed', details);
    chrome.storage.sync.set({
        apiUrl: CONFIG.API_BASE_URL,
        theme: 'dark',
        autoProcess: true
    });
});

// Check transcript function
async function checkTranscript(videoId) {
  try {
    // Validate video ID
    if (!videoId || typeof videoId !== 'string') {
      throw new Error('Invalid video ID');
    }

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

// Streaming function with full validation
async function askQuestionStream(videoId, question, onChunk, onError) {
  try {
    // CRITICAL: Validate video ID
    if (!videoId || typeof videoId !== 'string') {
      throw new Error('Invalid video ID');
    }
    
    videoId = videoId.trim();
    if (videoId.length === 0) {
      throw new Error('Video ID is empty');
    }
    
    // CRITICAL: Validate question
    if (!question || typeof question !== 'string') {
      throw new Error('Invalid question');
    }
    
    question = question.trim();
    if (question.length === 0) {
      throw new Error('Question is empty');
    }
    
    // Ensure both are clean strings
    videoId = String(videoId);
    question = String(question);

    const settings = await chrome.storage.sync.get(['apiUrl']);
    const apiUrl = settings.apiUrl || CONFIG.API_BASE_URL;

    console.log(`🔄 Starting stream for video ${videoId}`);
    console.log(`📝 Question: "${question}"`);

    const response = await fetch(`${apiUrl}/ask/stream`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({ 
        video_id: videoId, 
        question: question 
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error("No response body for streaming");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        console.log('✓ Stream completed');
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      // Split on SSE event boundaries
      const events = buffer.split("\n\n");
      buffer = events.pop(); // Keep incomplete event in buffer

      for (const event of events) {
        if (event.startsWith("data: ")) {
          const chunk = event.replace("data: ", "").trim();
          
          if (chunk === "[END]") {
            console.log('✓ Stream ended normally');
            return;
          }
          
          if (chunk.length > 0) {
            console.log('📦 Chunk received:', chunk.substring(0, 50) + (chunk.length > 50 ? '...' : ''));
            onChunk(chunk);
          }
        }
      }
    }
  } catch (error) {
    console.error('✗ Streaming error:', error);
    onError(error.message);
  }
}

// Message listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📩 Background received message:', request.type);
  
  // Handle transcript check
  if (request.type === 'CHECK_TRANSCRIPT') {
    const videoId = request.videoId;
    
    if (!videoId) {
      sendResponse({ success: false, error: 'No video ID provided' });
      return true;
    }
    
    checkTranscript(videoId)
      .then(sendResponse)
      .catch(err => sendResponse({ success: false, error: err.message }));
    
    return true; // Keep channel open for async response
  }
  
  // Handle streaming question
  if (request.type === 'ASK_QUESTION_STREAM') {
    const videoId = request.videoId;
    const question = request.question;
    
    // Validate inputs
    if (!videoId) {
      console.error('No video ID provided');
      return true;
    }
    
    if (!question) {
      console.error('No question provided');
      return true;
    }
    
    // Start streaming with validation
    askQuestionStream(
      videoId,
      question,
      (chunk) => {
        // Send chunk to content script (which forwards to sidebar)
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs && tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, { 
              type: 'STREAM_CHUNK', 
              chunk: chunk 
            }).catch(err => {
              console.error('Error sending chunk to tab:', err);
            });
          }
        });
      },
      (error) => {
        // Send error to content script
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs && tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, { 
              type: 'STREAM_ERROR', 
              error: error 
            }).catch(err => {
              console.error('Error sending error to tab:', err);
            });
          }
        });
      }
    );
    
    return true; // Keep channel open
  }
  
  // Unknown message type
  console.warn('Unknown message type:', request.type);
  return false;
});

// Connection listener
chrome.runtime.onConnect.addListener((port) => {
  console.log('🔌 Port connected:', port.name);
  
  port.onDisconnect.addListener(() => {
    console.log('🔌 Port disconnected:', port.name);
  });
});

// Startup log
console.log('🚀 VidIQAI Background Service Worker Started');
console.log('🌐 API Base URL:', CONFIG.API_BASE_URL);

// Handle service worker lifecycle
self.addEventListener('activate', (event) => {
  console.log('✓ Service Worker activated');
});

self.addEventListener('install', (event) => {
  console.log('✓ Service Worker installed');
  self.skipWaiting();
});
