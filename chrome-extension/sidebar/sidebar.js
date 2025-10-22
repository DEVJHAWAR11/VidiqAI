const chatContainer = document.getElementById('chat-container');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const transcriptStatus = document.getElementById('transcript-status');
const closeBtn = document.getElementById('close-btn');
const clearBtn = document.getElementById('clear-btn');
const emptyState = document.getElementById('empty-state');
const suggestions = document.getElementById('suggestions');
let videoId = null;

const progressBar = document.getElementById('progress-bar');
const progressFill = progressBar.querySelector('.progress-fill');

function showProgress(percentage) {
    progressBar.classList.add('active');
    progressFill.style.width = percentage + '%';
}

function hideProgress() {
    progressBar.classList.remove('active');
    progressFill.style.width = '0%';
}

// FIXED: Aggressive deduplication function
function removeConsecutiveDuplicates(text) {
    if (!text) return text;
    
    const words = text.split(/\s+/);
    const cleaned = [];
    let prevWord = null;
    
    for (let word of words) {
        if (!word) continue;
        
        const wordNormalized = word.replace(/[^\w]/g, '').toLowerCase();
        
        if (wordNormalized !== prevWord || wordNormalized === '') {
            cleaned.push(word);
            prevWord = wordNormalized;
        }
    }
    
    return cleaned.join(' ');
}

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

suggestions.addEventListener('click', (e) => {
    if (e.target.classList.contains('suggestion-chip')) {
        // FIXED: Direct text extraction without emoji removal
        let question = e.target.textContent.trim();
        
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

// FIXED: Robust copy to clipboard function
function copyToClipboard(text, button) {
    // Try modern Clipboard API first
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text)
            .then(() => {
                button.textContent = 'Copied!';
                button.style.backgroundColor = '#10b981';
                button.style.color = 'white';
                setTimeout(() => {
                    button.textContent = 'Copy';
                    button.style.backgroundColor = '';
                    button.style.color = '';
                }, 2000);
            })
            .catch(err => {
                console.error('Clipboard API failed:', err);
                // Fallback to execCommand
                fallbackCopy(text, button);
            });
    } else {
        // Use fallback for non-secure contexts
        fallbackCopy(text, button);
    }
}

// Fallback copy method using execCommand
function fallbackCopy(text, button) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            button.textContent = 'Copied!';
            button.style.backgroundColor = '#10b981';
            button.style.color = 'white';
            setTimeout(() => {
                button.textContent = 'Copy';
                button.style.backgroundColor = '';
                button.style.color = '';
            }, 2000);
        } else {
            button.textContent = 'Failed';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        }
    } catch (err) {
        console.error('Fallback copy failed:', err);
        button.textContent = 'Failed';
        setTimeout(() => {
            button.textContent = 'Copy';
        }, 2000);
    }
    
    document.body.removeChild(textArea);
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
        
        // FIXED: Proper copy button click handler
        copyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Get the text from the message-text span
            const messageTextEl = this.parentElement.querySelector('.message-text');
            if (messageTextEl) {
                const messageText = messageTextEl.textContent || messageTextEl.innerText || '';
                if (messageText) {
                    copyToClipboard(messageText, this);
                } else {
                    console.error('No text to copy');
                    this.textContent = 'Empty';
                    setTimeout(() => {
                        this.textContent = 'Copy';
                    }, 1500);
                }
            } else {
                console.error('Could not find message-text element');
            }
        });
        
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
    
    question = String(question);
    
    addMessage(question, 'user');
    chatInput.value = '';
    
    const botMsg = addMessage('', 'bot');
    const copyBtn = botMsg.querySelector('.copy-btn');
    if (copyBtn) {
        copyBtn.style.display = 'none';
    }
    
    chrome.runtime.sendMessage({
        type: 'ASK_QUESTION_STREAM',
        videoId: String(videoId),
        question: question
    });
});

// FIXED: Single message listener with proper deduplication
window.addEventListener("message", (event) => {
    if (event.data?.videoId) {
        videoId = event.data.videoId;
        checkTranscript();
    }
    
    if (event.data?.type === 'STREAM_CHUNK') {
        const chunk = String(event.data.chunk).trim();
        
        // Show progress during processing
        if (chunk.includes('Processing')) {
            showProgress(20);
        } else if (chunk.includes('Creating embeddings')) {
            showProgress(60);
        } else if (chunk.includes('Ready')) {
            showProgress(100);
            setTimeout(hideProgress, 500);
        }
        
        const lastMsg = chatContainer.querySelector('.message.bot:last-child');
        if (lastMsg) {
            const textSpan = lastMsg.querySelector('.message-text');
            if (textSpan) {
                const currentText = textSpan.textContent;
                const newText = chunk;
                
                // Concatenate with single space and deduplicate
                if (currentText && currentText.length > 0) {
                    const combined = currentText + ' ' + newText;
                    textSpan.textContent = removeConsecutiveDuplicates(combined);
                } else {
                    textSpan.textContent = newText;
                }
                
                // Show copy button once text starts appearing
                const copyBtn = lastMsg.querySelector('.copy-btn');
                if (copyBtn && textSpan.textContent.length > 10) {
                    copyBtn.style.display = 'block';
                }
            }
            
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    if (event.data?.type === 'STREAM_ERROR') {
        const lastMsg = chatContainer.querySelector('.message.bot:last-child');
        if (lastMsg) {
            const textSpan = lastMsg.querySelector('.message-text');
            if (textSpan) {
                textSpan.textContent = `❌ ${event.data.error}`;
                textSpan.style.color = '#f23b3b';
            }
        }
    }
});
