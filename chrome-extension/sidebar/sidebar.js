const chatContainer = document.getElementById('chat-container');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const transcriptStatus = document.getElementById('transcript-status');
const closeBtn = document.getElementById('close-btn');
const clearBtn = document.getElementById('clear-btn');
const emptyState = document.getElementById('empty-state');
const suggestions = document.getElementById('suggestions');

let videoId = null;

closeBtn.addEventListener('click', (e) => {
  e.preventDefault();
  window.parent.postMessage({ type: 'CLOSE_SIDEBAR' }, '*');
});

clearBtn.addEventListener('click', () => {
  const messages = chatContainer.querySelectorAll('.message');
  messages.forEach(msg => msg.remove());
  emptyState.classList.remove('hidden');
  suggestions.style.display = 'flex';
});

// FIXED: Suggestion chip handler with proper text extraction
suggestions.addEventListener('click', (e) => {
  if (e.target.classList.contains('suggestion-chip')) {
    // Extract only the text, remove all emojis and trim
    let question = e.target.textContent
      .replace(/[\u{1F300}-\u{1F9FF}]/gu, '') // Remove all emojis
      .replace(/^[📝💡⏱️🔥⚡]\s*/, '') // Remove specific emojis
      .trim();
    
    if (question && question.length > 0) {
      chatInput.value = question;
      chatForm.dispatchEvent(new Event('submit'));
    }
  }
});

function setTranscriptStatus(status, color = '#aaaaaa') {
  transcriptStatus.textContent = status;
  transcriptStatus.style.color = color;
}

function addMessage(text, sender = 'bot') {
  emptyState.classList.add('hidden');
  suggestions.style.display = 'none';
  
  const msg = document.createElement('div');
  msg.className = `message ${sender}`;
  
  if (sender === 'bot') {
    const textSpan = document.createElement('span');
    textSpan.className = 'message-text';
    textSpan.textContent = text;
    
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = 'Copy';
    copyBtn.onclick = function() {
      const messageText = this.previousElementSibling.textContent;
      navigator.clipboard.writeText(messageText).then(() => {
        this.textContent = 'Copied!';
        setTimeout(() => {
          this.textContent = 'Copy';
        }, 2000);
      });
    };
    
    msg.appendChild(textSpan);
    msg.appendChild(copyBtn);
  } else {
    msg.textContent = text;
  }
  
  chatContainer.appendChild(msg);
  chatContainer.scrollTop = chatContainer.scrollHeight;
  return msg;
}

function checkTranscript() {
  if (!videoId) {
    setTranscriptStatus('No video found', '#f23b3b');
    return;
  }
  
  setTranscriptStatus('Checking...');
  chrome.runtime.sendMessage(
    { type: 'CHECK_TRANSCRIPT', videoId },
    (response) => {
      if (response && response.success) {
        setTranscriptStatus('✅ Ready to chat');
      } else {
        setTranscriptStatus('❌ Error', '#f23b3b');
      }
    }
  );
}

chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  
  // CRITICAL: Validate and clean question
  let question = chatInput.value;
  if (!question || typeof question !== 'string') {
    console.error('Invalid question:', question);
    return;
  }
  
  question = question.trim();
  if (question.length === 0) {
    console.error('Empty question');
    return;
  }
  
  // Ensure it's a valid string
  question = String(question);
  
  addMessage(question, 'user');
  chatInput.value = '';
  const botMsg = addMessage('', 'bot');
  botMsg.querySelector('.copy-btn').style.display = 'none';

  // Send as plain object with validated string
  chrome.runtime.sendMessage({
    type: 'ASK_QUESTION_STREAM',
    videoId: String(videoId),
    question: question
  });
});

window.addEventListener("message", (event) => {
  if (event.data?.videoId) {
    videoId = event.data.videoId;
    checkTranscript();
  }
  
  if (event.data?.type === 'STREAM_CHUNK') {
    const lastMsg = chatContainer.querySelector('.message.bot:last-child .message-text');
    if (lastMsg) {
      const currentText = lastMsg.textContent;
      const newText = String(event.data.chunk).trim();
      
      if (currentText && currentText.length > 0) {
        lastMsg.textContent = currentText + ' ' + newText;
      } else {
        lastMsg.textContent = newText;
      }
      
      // Show copy button once text is complete
      const copyBtn = lastMsg.nextElementSibling;
      if (copyBtn && copyBtn.classList.contains('copy-btn')) {
        copyBtn.style.display = 'block';
      }
      
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }
  
  if (event.data?.type === 'STREAM_ERROR') {
    const lastMsg = chatContainer.querySelector('.message.bot:last-child .message-text');
    if (lastMsg) {
      lastMsg.textContent = `❌ ${event.data.error}`;
      lastMsg.style.color = '#f23b3b';
    }
  }
});
