const chatContainer = document.getElementById('chat-container');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const transcriptStatus = document.getElementById('transcript-status');

let videoId = null;

// Utility to get video ID from parent page
function getVideoIdFromParent() {
  try {
    const url = new URL(document.referrer || window.parent.location.href);
    return url.searchParams.get('v');
  } catch {
    return null;
  }
}

// Show transcript status
function setTranscriptStatus(status, color = '#6366f1') {
  transcriptStatus.textContent = status;
  transcriptStatus.style.color = color;
}

// Add message to chat
function addMessage(text, sender = 'bot') {
  const msg = document.createElement('div');
  msg.className = `message ${sender}`;
  msg.textContent = text;
  chatContainer.appendChild(msg);
  chatContainer.scrollTop = chatContainer.scrollHeight;
  return msg;
}

// Check transcript status
function checkTranscript() {
  setTranscriptStatus('Checking transcript...');
  chrome.runtime.sendMessage(
    { type: 'CHECK_TRANSCRIPT', videoId },
    (response) => {
      if (response && response.success) {
        if (response.data.status === 'available') {
          setTranscriptStatus('Transcript available. Ask anything!');
        } else if (response.data.status === 'fetching') {
          setTranscriptStatus('Transcript not found. Fetching audio...');
        } else {
          setTranscriptStatus('Transcript unavailable for this video.', '#e11d48');
        }
      } else {
        setTranscriptStatus('Error checking transcript.', '#e11d48');
      }
    }
  );
}

// Streaming chat submit handler
chatForm.onsubmit = (e) => {
  e.preventDefault();
  const question = chatInput.value.trim();
  if (!question) return;
  addMessage(question, 'user');
  chatInput.value = '';
  // Add a new bot message for streaming
  addMessage('', 'bot');

  // Use streaming
  chrome.runtime.sendMessage(
    { type: 'ASK_QUESTION_STREAM', videoId, question },
    () => {
      // No callback needed for streaming
    }
  );
};

// Listen for streaming chunks from background
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'STREAM_CHUNK') {
    // Append chunk to last bot message
    const lastBotMsg = chatContainer.querySelector('.message.bot:last-child');
    if (lastBotMsg) lastBotMsg.textContent += msg.chunk;
  }
});

window.onload = () => {
  videoId = getVideoIdFromParent();
  if (!videoId) {
    setTranscriptStatus('Could not detect video ID.', '#e11d48');
    chatForm.style.display = 'none';
    return;
  }
  checkTranscript();
};
