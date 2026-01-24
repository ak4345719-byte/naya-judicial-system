

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const msgInput = document.getElementById('msgInput');
    const chatContainer = document.getElementById('chatContainer');
    const caseInput = document.getElementById('caseInput');
    const currentCaseDisplay = document.getElementById('currentCaseDisplay');
    const voiceBtn = document.getElementById('voiceBtn');
    const languageSelect = document.getElementById('languageSelect');

    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isListening = false;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';
        recognition.interimResults = false;

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            msgInput.value = transcript;
            voiceBtn.classList.remove('bg-red-500', 'text-white', 'animate-pulse');
            voiceBtn.classList.add('bg-gray-200', 'text-gray-700');
            isListening = false;
        };

        recognition.onerror = (event) => {
            console.error("Speech error", event);
            voiceBtn.classList.remove('bg-red-500', 'text-white', 'animate-pulse');
            voiceBtn.classList.add('bg-gray-200', 'text-gray-700');
            isListening = false;
        };

        recognition.onend = () => {
            if (isListening) {
                voiceBtn.classList.remove('bg-red-500', 'text-white', 'animate-pulse');
                voiceBtn.classList.add('bg-gray-200', 'text-gray-700');
                isListening = false;
            }
        };

        voiceBtn.addEventListener('click', () => {
            if (!isListening) {
                recognition.start();
                isListening = true;
                voiceBtn.classList.remove('bg-gray-200', 'text-gray-700');
                voiceBtn.classList.add('bg-red-500', 'text-white', 'animate-pulse');
            } else {
                recognition.stop();
                isListening = false;
                voiceBtn.classList.remove('bg-red-500', 'text-white', 'animate-pulse');
                voiceBtn.classList.add('bg-gray-200', 'text-gray-700');
            }
        });
    } else {
        voiceBtn.style.display = 'none'; 
    }

    const voiceToggle = document.getElementById('voiceToggle');

    
    let isVoiceEnabled = localStorage.getItem('voiceEnabled') !== 'false'; 
    if (voiceToggle) {
        voiceToggle.checked = isVoiceEnabled;
        voiceToggle.addEventListener('change', () => {
            isVoiceEnabled = voiceToggle.checked;
            localStorage.setItem('voiceEnabled', isVoiceEnabled);
            if (!isVoiceEnabled) {
                window.speechSynthesis.cancel(); 
            }
        });
    }

    
    const speakText = (text) => {
        if (!isVoiceEnabled) return; 

        if ('speechSynthesis' in window) {
            
            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            
            const selectedLang = languageSelect.value;
            if (selectedLang === "Hindi") utterance.lang = "hi-IN";
            else if (selectedLang === "Kannada") utterance.lang = "kn-IN";
            else utterance.lang = "en-US";

            window.speechSynthesis.speak(utterance);
        }
    };

    
    caseInput.addEventListener('input', () => {
        const val = caseInput.value.trim();
        currentCaseDisplay.textContent = val ? `Active Context: ${val}` : "No case selected";
    });

    
    const scrollToBottom = () => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    };

    
    const addMessage = (text, isUser = false) => {
        const div = document.createElement('div');
        div.className = `flex gap-3 chat-msg ${isUser ? 'flex-row-reverse' : ''} mb-4`;

        const avatar = isUser
            ? `<div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 flex-shrink-0 shadow-sm"><i class="fas fa-user"></i></div>`
            : `<div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0 shadow-sm"><i class="fas fa-robot"></i></div>`;

        const bubbleClass = isUser
            ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-2xl rounded-tr-sm shadow-md'
            : 'bg-white text-gray-800 border-none shadow-sm rounded-2xl rounded-tl-sm ring-1 ring-gray-100';

        div.innerHTML = `
            ${avatar}
            <div class="px-5 py-3.5 max-w-[80%] leading-relaxed text-sm ${bubbleClass}">
                ${text.replace(/\n/g, '<br>')}
            </div>
        `;

        chatContainer.appendChild(div);
        scrollToBottom();
    };

    
    const renderSuggestions = () => {
        const id = 'suggestions-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'flex gap-2 flex-wrap ml-11 mb-4 animate-fade-in-up';

        const suggestions = [
            "Summarize the case facts",
            "List key evidence",
            "What are the charges?",
            "Draft a bail order"
        ];

        div.innerHTML = suggestions.map(s => `
            <button onclick="fillAndSend('${s}')" 
                class="text-xs bg-white hover:bg-indigo-50 text-indigo-600 border border-indigo-100 px-3 py-1.5 rounded-full transition-all shadow-sm hover:shadow-md cursor-pointer whitespace-nowrap">
                ${s}
            </button>
        `).join('');

        chatContainer.appendChild(div);
        scrollToBottom();
    };

    
    window.fillAndSend = (text) => {
        msgInput.value = text;
        
        
        msgInput.focus();
    };

    
    const addLoading = () => {
        const id = 'loading-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'flex gap-3 chat-msg mb-4';
        div.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0"><i class="fas fa-robot"></i></div>
            <div class="bg-white px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm ring-1 ring-gray-100">
                <div class="flex gap-1.5 items-center h-full">
                    <div class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></div>
                    <div class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
            </div>
        `;
        chatContainer.appendChild(div);
        scrollToBottom();
        return id;
    };

    
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msg = msgInput.value.trim();
        const caseNum = caseInput.value.trim();
        const selectedModel = document.getElementById('modelSelect').value;
        const selectedLanguage = document.getElementById('languageSelect').value;

        if (!msg) return;
        if (!caseNum) {
            
            alert("Please enter a Case Number in the sidebar first.");
            caseInput.focus();
            return;
        }

        
        const oldSugg = document.querySelectorAll('[id^="suggestions-"]');
        oldSugg.forEach(el => el.remove());

        
        addMessage(msg, true);
        msgInput.value = '';

        
        const loadingId = addLoading();

        try {
            const res = await fetch('/api/chat/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: msg,
                    case_number: caseNum,
                    model: selectedModel,
                    language: selectedLanguage
                })
            });
            const data = await res.json();

            
            const loader = document.getElementById(loadingId);
            if (loader) loader.remove();

            if (data.answer) {
                addMessage(data.answer);
                speakText(data.answer); 
                
                setTimeout(renderSuggestions, 1000);
            } else {
                addMessage("I'm sorry, I encountered an error: " + (data.error || "Unknown error"));
            }

        } catch (err) {
            const loader = document.getElementById(loadingId);
            if (loader) loader.remove();
            addMessage("Network error. Please ensure the server and Ollama are running.");
        }
    });

    window.clearChat = () => {
        chatContainer.innerHTML = '';
        const greeting = `
            <div class="flex gap-3 chat-msg mb-4">
                <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0 shadow-sm">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="bg-white px-5 py-3.5 max-w-[80%] leading-relaxed text-sm text-gray-800 border-none shadow-sm rounded-2xl rounded-tl-sm ring-1 ring-gray-100">
                    Hello, Your Honor. I am your AI Legal Assistant. Please enter a Case Number in the sidebar to begin.
                </div>
            </div>
        `;
        chatContainer.innerHTML = greeting;
        renderSuggestions();
    };

    
    renderSuggestions();
});
