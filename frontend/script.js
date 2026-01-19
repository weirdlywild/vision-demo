// Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let currentSessionId = null;
let currentImageFile = null;

// DOM Elements
const chatContainer = document.getElementById('chatContainer');
const uploadZone = document.getElementById('uploadZone');
const imageInput = document.getElementById('imageInput');
const messageContainer = document.getElementById('messageContainer');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const sessionInfo = document.getElementById('sessionInfo');
const sessionIdDisplay = document.getElementById('sessionId');
const newSessionBtn = document.getElementById('newSessionBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    // Upload zone click
    uploadZone.addEventListener('click', () => {
        imageInput.click();
    });

    // File input change
    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleImageUpload(file);
        }
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');

        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleImageUpload(file);
        }
    });

    // Send message
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !sendButton.disabled) {
            sendMessage();
        }
    });

    // New session
    newSessionBtn.addEventListener('click', resetSession);
}

async function handleImageUpload(file) {
    currentImageFile = file;

    // Hide welcome message if it's the first message
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Display user's image message
    const imageUrl = URL.createObjectURL(file);
    addUserMessage('', imageUrl);

    // Show status
    const statusId = showStatus('Processing image...');

    // Create form data
    const formData = new FormData();
    formData.append('image', file);

    if (currentSessionId) {
        formData.append('session_id', currentSessionId);
    }

    try {
        // Update status
        updateStatus(statusId, 'Analyzing with AI...');

        // Send request
        const response = await fetch(`${API_BASE_URL}/diagnose`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Remove status
        removeStatus(statusId);

        // Display diagnosis
        displayDiagnosis(data);

        // Store session ID
        if (data.session_id) {
            currentSessionId = data.session_id;
            showSessionInfo();
        }

        // Enable follow-up questions
        enableFollowUp();

    } catch (error) {
        removeStatus(statusId);
        addAssistantMessage('❌ Error: ' + error.message);
        console.error('Error:', error);
    }
}

async function sendMessage() {
    const question = messageInput.value.trim();
    if (!question || !currentSessionId) return;

    // Display user's message
    addUserMessage(question);
    messageInput.value = '';

    // Show status
    const statusId = showStatus('Thinking...');

    // Create form data
    const formData = new FormData();
    formData.append('session_id', currentSessionId);
    formData.append('question', question);

    try {
        const response = await fetch(`${API_BASE_URL}/diagnose`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Remove status
        removeStatus(statusId);

        // Display updated diagnosis
        displayDiagnosis(data, true);

    } catch (error) {
        removeStatus(statusId);
        addAssistantMessage('❌ Error: ' + error.message);
        console.error('Error:', error);
    }
}

function displayDiagnosis(data, isFollowUp = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';

    let html = '<div class="message-content">';

    // Timing Info (prominent)
    if (data.timing) {
        html += formatTimingInfo(data.timing);
    }

    // Diagnosis Content
    if (!isFollowUp) {
        html += '<div class="diagnosis-content">';

        // Header
        html += '<div class="diagnosis-header">';
        html += `<div class="diagnosis-title">📋 ${data.diagnosis}</div>`;
        html += `<div>Confidence: ${(data.confidence * 100).toFixed(0)}%</div>`;
        html += '<div class="confidence-bar">';
        html += `<div class="confidence-fill" style="width: ${data.confidence * 100}%"></div>`;
        html += '</div>';
        html += '</div>';

        // Materials
        if (data.materials && data.materials.length > 0) {
            html += '<div class="section">';
            html += '<div class="section-title">🛒 Materials Needed</div>';
            html += '<ul class="materials-list">';
            data.materials.forEach(mat => {
                html += `<li>
                    <div><strong>${mat.name}</strong></div>
                    <div class="material-category">${mat.category}</div>
                </li>`;
            });
            html += '</ul>';
            html += '</div>';
        }

        // Tools
        if (data.tools_required && data.tools_required.length > 0) {
            html += '<div class="section">';
            html += '<div class="section-title">🔧 Tools Required</div>';
            html += '<ul class="tools-list">';
            data.tools_required.forEach(tool => {
                html += `<li>${tool}</li>`;
            });
            html += '</ul>';
            html += '</div>';
        }

        // Repair Steps
        if (data.repair_steps && data.repair_steps.length > 0) {
            html += '<div class="section">';
            html += '<div class="section-title">📝 Repair Steps</div>';
            data.repair_steps.forEach(step => {
                html += `<div class="repair-step">
                    <div class="step-title">
                        <span class="step-number">Step ${step.step}:</span>
                        ${step.title}
                    </div>
                    <div class="step-instruction">${step.instruction}</div>`;
                if (step.safety_tip) {
                    html += `<div class="safety-tip">⚠️ ${step.safety_tip}</div>`;
                }
                html += '</div>';
            });
            html += '</div>';
        }

        // Warnings
        if (data.warnings && data.warnings.length > 0) {
            html += '<div class="section">';
            html += '<div class="section-title">⚠️ Safety Warnings</div>';
            data.warnings.forEach(warning => {
                html += `<div class="warning">${warning}</div>`;
            });
            html += '</div>';
        }

        // Follow-up Questions
        if (data.followup_questions && data.followup_questions.length > 0) {
            html += '<div class="followup-questions">';
            html += '<div class="section-title">💭 Questions you might ask:</div>';
            data.followup_questions.forEach(q => {
                html += `<span class="question-chip" onclick="askQuestion('${escapeHtml(q)}')">${q}</span>`;
            });
            html += '</div>';
        }

        html += '</div>'; // diagnosis-content
    } else {
        // For follow-up responses, show simplified view
        html += `<p><strong>Updated information:</strong></p>`;
        html += `<p>${data.diagnosis}</p>`;

        // Show any new materials/steps
        if (data.materials && data.materials.length > 0) {
            html += '<p><strong>Materials:</strong></p><ul>';
            data.materials.forEach(mat => {
                html += `<li>${mat.name}</li>`;
            });
            html += '</ul>';
        }
    }

    html += '</div>'; // message-content

    messageDiv.innerHTML = html;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function formatTimingInfo(timing) {
    const timingId = 'timing-' + Date.now();

    // Calculate OpenAI cost (GPT-4o Vision pricing)
    const openaiCost = calculateOpenAICost(timing);

    let html = '<div class="timing-info-compact">';
    html += `<span class="info-icon" onclick="toggleTimingDetails('${timingId}')">ℹ️ Details</span>`;
    html += `<span class="timing-summary">${timing.total_time.toFixed(2)}s`;

    if (timing.cache_source) {
        let badgeText = timing.cache_source;
        if (badgeText === 'exact') badgeText = 'Cached';
        else if (badgeText === 'perceptual') badgeText = 'Similar cached';
        else if (badgeText === 'miss') badgeText = 'New';
        else if (badgeText === 'followup') badgeText = 'Follow-up';
        html += ` • ${badgeText}`;
    }

    html += '</span>';
    html += '</div>';

    // Hidden details panel
    html += `<div class="timing-details" id="${timingId}" style="display: none;">`;
    html += '<div class="timing-details-content">';

    // Performance Metrics Section
    html += '<div class="details-section">';
    html += '<div class="section-header">⏱️ Performance Metrics</div>';
    html += '<div class="timing-row">';
    html += '<span class="timing-label"><strong>Total Time</strong></span>';
    html += `<span class="timing-value"><strong>${timing.total_time.toFixed(2)}s</strong></span>`;
    html += '</div>';

    if (timing.image_processing_time > 0) {
        html += '<div class="timing-row">';
        html += '<span class="timing-label">Image Processing</span>';
        html += `<span class="timing-value">${timing.image_processing_time.toFixed(3)}s</span>`;
        html += '</div>';
    }

    if (timing.cache_lookup_time > 0) {
        html += '<div class="timing-row">';
        html += '<span class="timing-label">Cache Lookup</span>';
        html += `<span class="timing-value">${timing.cache_lookup_time.toFixed(3)}s</span>`;
        html += '</div>';
    }

    if (timing.openai_api_time > 0) {
        html += '<div class="timing-row">';
        html += '<span class="timing-label">OpenAI API Call</span>';
        html += `<span class="timing-value">${timing.openai_api_time.toFixed(3)}s</span>`;
        html += '</div>';
    }

    if (timing.normalization_time > 0) {
        html += '<div class="timing-row">';
        html += '<span class="timing-label">Material Normalization</span>';
        html += `<span class="timing-value">${timing.normalization_time.toFixed(3)}s</span>`;
        html += '</div>';
    }
    html += '</div>'; // details-section

    // OpenAI Pricing Section
    if (timing.openai_api_time > 0) {
        html += '<div class="details-section">';
        html += '<div class="section-header">💰 OpenAI Cost Estimate</div>';
        html += '<div class="timing-row">';
        html += '<span class="timing-label">Model</span>';
        html += '<span class="timing-value">GPT-4o Vision</span>';
        html += '</div>';
        html += '<div class="timing-row">';
        html += '<span class="timing-label">Estimated Cost</span>';
        html += `<span class="timing-value">~$${openaiCost.total.toFixed(4)}</span>`;
        html += '</div>';
        html += '<div class="timing-row small">';
        html += '<span class="timing-label">Input Tokens</span>';
        html += `<span class="timing-value">${openaiCost.input_tokens} (~$${openaiCost.input_cost.toFixed(4)})</span>`;
        html += '</div>';
        html += '<div class="timing-row small">';
        html += '<span class="timing-label">Output Tokens</span>';
        html += `<span class="timing-value">${openaiCost.output_tokens} (~$${openaiCost.output_cost.toFixed(4)})</span>`;
        html += '</div>';
        html += '<div class="cost-note">* Approximate based on typical usage</div>';
        html += '</div>'; // details-section
    }

    // Cache Status Section
    html += '<div class="details-section">';
    html += '<div class="section-header">📦 Cache Status</div>';
    html += '<div class="timing-row">';
    html += '<span class="timing-label">Source</span>';

    let cacheDescription = '';
    if (timing.cache_source === 'exact') {
        cacheDescription = 'Exact match - No API cost';
    } else if (timing.cache_source === 'perceptual') {
        cacheDescription = 'Similar image - No API cost';
    } else if (timing.cache_source === 'miss') {
        cacheDescription = 'New diagnosis - API cost incurred';
    } else if (timing.cache_source === 'followup') {
        cacheDescription = 'Follow-up question - API cost incurred';
    } else {
        cacheDescription = 'Unknown';
    }

    html += `<span class="timing-value">${cacheDescription}</span>`;
    html += '</div>';
    html += '</div>'; // details-section

    html += '</div>'; // timing-details-content
    html += '</div>'; // timing-details

    return html;
}

function calculateOpenAICost(timing) {
    // GPT-4o Vision pricing (as of 2024)
    // Input: $2.50 per 1M tokens
    // Output: $10.00 per 1M tokens

    const INPUT_COST_PER_TOKEN = 2.50 / 1_000_000;
    const OUTPUT_COST_PER_TOKEN = 10.00 / 1_000_000;

    // Estimate token usage based on typical requests
    // Image analysis typically uses ~1000-1500 input tokens (including image)
    // Diagnosis output typically uses ~800-1500 output tokens

    let input_tokens = 0;
    let output_tokens = 0;

    if (timing.openai_api_time > 0) {
        // Estimate based on request type
        if (timing.cache_source === 'followup') {
            input_tokens = 500;  // Smaller context for follow-ups
            output_tokens = 400;
        } else {
            input_tokens = 1200; // Image + prompts
            output_tokens = 1000; // Full diagnosis
        }
    }

    const input_cost = input_tokens * INPUT_COST_PER_TOKEN;
    const output_cost = output_tokens * OUTPUT_COST_PER_TOKEN;
    const total = input_cost + output_cost;

    return {
        input_tokens,
        output_tokens,
        input_cost,
        output_cost,
        total
    };
}

function toggleTimingDetails(timingId) {
    const detailsPanel = document.getElementById(timingId);
    if (detailsPanel) {
        if (detailsPanel.style.display === 'none') {
            detailsPanel.style.display = 'block';
        } else {
            detailsPanel.style.display = 'none';
        }
    }
}

function addUserMessage(text, imageUrl = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';

    let html = '<div class="message-content">';
    if (imageUrl) {
        html += `<img src="${imageUrl}" alt="Uploaded image" class="message-image">`;
    }
    if (text) {
        html += `<p>${escapeHtml(text)}</p>`;
    }
    html += '</div>';

    messageDiv.innerHTML = html;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function addAssistantMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function showStatus(text) {
    const statusId = 'status-' + Date.now();
    const statusDiv = document.createElement('div');
    statusDiv.id = statusId;
    statusDiv.className = 'status-message';
    statusDiv.innerHTML = `
        <span class="status-spinner"></span>
        <span class="status-text">${text}</span>
    `;
    chatContainer.appendChild(statusDiv);
    scrollToBottom();
    return statusId;
}

function updateStatus(statusId, text) {
    const statusDiv = document.getElementById(statusId);
    if (statusDiv) {
        const textSpan = statusDiv.querySelector('.status-text');
        if (textSpan) {
            textSpan.textContent = text;
        }
    }
}

function removeStatus(statusId) {
    const statusDiv = document.getElementById(statusId);
    if (statusDiv) {
        statusDiv.remove();
    }
}

function enableFollowUp() {
    uploadZone.style.display = 'none';
    messageContainer.style.display = 'flex';
    messageInput.disabled = false;
    sendButton.disabled = false;
    messageInput.focus();
}

function showSessionInfo() {
    sessionInfo.style.display = 'flex';
    sessionIdDisplay.textContent = currentSessionId.substring(0, 8) + '...';
}

function resetSession() {
    currentSessionId = null;
    currentImageFile = null;

    chatContainer.innerHTML = `
        <div class="welcome-message">
            <div class="icon">🛠️</div>
            <h2>Welcome!</h2>
            <p>I'm your AI repair assistant. Upload a photo of a broken household item, and I'll:</p>
            <ul>
                <li>Diagnose what's wrong</li>
                <li>Provide step-by-step repair instructions</li>
                <li>List materials and tools you'll need</li>
                <li>Give you safety warnings</li>
            </ul>
            <p class="hint">Click the button below or drag & drop an image to get started!</p>
        </div>
    `;

    uploadZone.style.display = 'block';
    messageContainer.style.display = 'none';
    sessionInfo.style.display = 'none';
    messageInput.value = '';
    messageInput.disabled = true;
    sendButton.disabled = true;
}

function askQuestion(question) {
    messageInput.value = question;
    sendMessage();
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
