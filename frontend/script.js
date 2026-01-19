// Configuration
// Automatically use current domain for API calls (works locally and on Railway)
const API_BASE_URL = window.location.origin;
const AUTH_STORAGE_KEY = 'diy_repair_auth_password';

// State
let currentSessionId = null;
let currentImageFile = null;
let apiPassword = null;

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
const authModal = document.getElementById('authModal');
const authForm = document.getElementById('authForm');
const passwordInput = document.getElementById('passwordInput');
const authError = document.getElementById('authError');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuthentication();
    setupEventListeners();
});

// Authentication Functions
function checkAuthentication() {
    // Check if password is stored in localStorage
    const storedPassword = localStorage.getItem(AUTH_STORAGE_KEY);

    if (storedPassword) {
        apiPassword = storedPassword;
        hideAuthModal();
    } else {
        showAuthModal();
    }
}

function showAuthModal() {
    authModal.style.display = 'flex';
    passwordInput.focus();
}

function hideAuthModal() {
    authModal.style.display = 'none';
}

async function validatePassword(password) {
    // Test the password by making a test request
    try {
        const formData = new FormData();
        // Create a tiny test image (1x1 transparent PNG)
        const testImageBlob = await fetch('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
            .then(res => res.blob());
        formData.append('image', testImageBlob, 'test.png');

        const response = await fetch(`${API_BASE_URL}/diagnose`, {
            method: 'POST',
            headers: {
                'X-API-Password': password
            },
            body: formData
        });

        // If we get 401 or 403, password is invalid
        if (response.status === 401 || response.status === 403) {
            return false;
        }

        // Any other response means password was accepted (even if image fails validation)
        return true;
    } catch (error) {
        // Network error - assume password might be valid
        console.error('Validation error:', error);
        return true;
    }
}

function showAuthError(message) {
    authError.textContent = message;
    authError.style.display = 'block';
}

function setupEventListeners() {
    // Auth form submit
    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const password = passwordInput.value.trim();

        if (!password) {
            showAuthError('Please enter a password');
            return;
        }

        // Show loading state
        const submitBtn = authForm.querySelector('button');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Verifying...';
        submitBtn.disabled = true;

        // Validate password
        const isValid = await validatePassword(password);

        if (isValid) {
            // Store password and close modal
            localStorage.setItem(AUTH_STORAGE_KEY, password);
            apiPassword = password;
            hideAuthModal();
            authError.style.display = 'none';
        } else {
            showAuthError('Invalid password. Please try again.');
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            passwordInput.value = '';
            passwordInput.focus();
        }
    });

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

    // Get selected model
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        formData.append('model', modelSelect.value);
    }

    if (currentSessionId) {
        formData.append('session_id', currentSessionId);
    }

    try {
        // Update status
        updateStatus(statusId, 'Analyzing with AI...');

        // Send request with authentication
        const response = await fetch(`${API_BASE_URL}/diagnose`, {
            method: 'POST',
            headers: {
                'X-API-Password': apiPassword
            },
            body: formData
        });

        if (!response.ok) {
            // Handle authentication errors
            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem(AUTH_STORAGE_KEY);
                apiPassword = null;
                showAuthModal();
                throw new Error('Authentication failed. Please log in again.');
            }
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

    // Create a tiny 1x1 transparent PNG as a dummy image for follow-up questions
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    canvas.toBlob(blob => {
        formData.append('image', blob, 'dummy.png');
        sendFollowupRequest(formData, statusId);
    }, 'image/png');
}

async function sendFollowupRequest(formData, statusId) {
    try {
        const response = await fetch(`${API_BASE_URL}/diagnose`, {
            method: 'POST',
            headers: {
                'X-API-Password': apiPassword
            },
            body: formData
        });

        if (!response.ok) {
            // Handle authentication errors
            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem(AUTH_STORAGE_KEY);
                apiPassword = null;
                showAuthModal();
                throw new Error('Authentication failed. Please log in again.');
            }
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

        // Professional help warning (if needed)
        if (data.professional_help_recommended && data.professional_help_recommended !== 'none') {
            html += '<div class="professional-warning">';
            html += `<div class="warning-icon">⚠️</div>`;
            html += `<div>`;
            html += `<strong>Professional Help Recommended: ${data.professional_help_recommended}</strong>`;
            if (data.professional_help_reason) {
                html += `<div class="reason">${data.professional_help_reason}</div>`;
            }
            html += `</div>`;
            html += '</div>';
        }

        // Quick info (estimated time, difficulty)
        if (data.estimated_time || data.difficulty) {
            html += '<div class="quick-info">';
            if (data.estimated_time) {
                html += `<span class="info-badge">⏱️ ${data.estimated_time}</span>`;
            }
            if (data.difficulty) {
                const difficultyEmoji = {
                    'easy': '✅',
                    'moderate': '⚙️',
                    'hard': '🔥'
                }[data.difficulty] || '⚙️';
                html += `<span class="info-badge">${difficultyEmoji} ${data.difficulty.charAt(0).toUpperCase() + data.difficulty.slice(1)}</span>`;
            }
            html += '</div>';
        }

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
        // For follow-up responses, show enhanced view
        html += '<div class="followup-content">';

        html += `<div class="section-title">💬 Answer</div>`;
        html += `<p>${data.diagnosis}</p>`;

        // Professional help warning (if present in followup)
        if (data.professional_help_recommended && data.professional_help_recommended !== 'none') {
            html += '<div class="professional-warning">';
            html += `<div class="warning-icon">⚠️</div>`;
            html += `<div>`;
            html += `<strong>Professional Help Recommended: ${data.professional_help_recommended}</strong>`;
            if (data.professional_help_reason) {
                html += `<div class="reason">${data.professional_help_reason}</div>`;
            }
            html += `</div>`;
            html += '</div>';
        }

        // Show any new materials
        if (data.materials && data.materials.length > 0) {
            html += '<div class="section">';
            html += '<div class="section-title">🛒 Additional Materials</div>';
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

        // Show any new steps
        if (data.repair_steps && data.repair_steps.length > 0) {
            html += '<div class="section">';
            html += '<div class="section-title">📝 Additional Steps</div>';
            html += '<ol class="steps-list">';
            data.repair_steps.forEach(step => {
                html += `<li>
                    <strong>${step.title}</strong>
                    <p>${step.instruction}</p>
                    ${step.safety_tip ? `<div class="safety-tip">💡 ${step.safety_tip}</div>` : ''}
                </li>`;
            });
            html += '</ol>';
            html += '</div>';
        }

        // Show any warnings
        if (data.warnings && data.warnings.length > 0) {
            html += '<div class="section warnings-section">';
            html += '<div class="section-title">⚠️ Safety Warnings</div>';
            html += '<ul class="warnings-list">';
            data.warnings.forEach(warning => {
                html += `<li>${warning}</li>`;
            });
            html += '</ul>';
            html += '</div>';
        }

        html += '</div>'; // followup-content
    }

    html += '</div>'; // message-content

    messageDiv.innerHTML = html;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function getModelPricing(model) {
    // OpenAI pricing as of January 2026 (per 1M tokens)
    const pricingTable = {
        'gpt-4o': { input: 2.50, output: 10.00 },
        'gpt-4o-2024-11-20': { input: 2.50, output: 10.00 },
        'gpt-4o-2024-08-06': { input: 2.50, output: 10.00 },
        'gpt-4o-2024-05-13': { input: 5.00, output: 15.00 },
        'gpt-4o-mini': { input: 0.15, output: 0.60 },
        'gpt-4o-mini-2024-07-18': { input: 0.15, output: 0.60 },
        'gpt-5': { input: 5.00, output: 15.00 },  // Estimated pricing
        'gpt-5-preview': { input: 5.00, output: 15.00 },
        'gpt-5-turbo': { input: 2.50, output: 10.00 }
    };

    return pricingTable[model] || { input: 2.50, output: 10.00 };
}

function formatTimingInfo(timing) {
    const timingId = 'timing-' + Date.now();

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

    // OpenAI Pricing Section - Real data from API
    if (timing.usage && timing.openai_api_time > 0) {
        html += '<div class="details-section">';
        html += '<div class="section-header">💰 OpenAI API Cost (Actual)</div>';
        html += '<div class="timing-row">';
        html += '<span class="timing-label">Model</span>';
        html += `<span class="timing-value">${timing.usage.model}</span>`;
        html += '</div>';

        // Calculate actual cost based on model pricing
        const pricing = getModelPricing(timing.usage.model);
        const inputCost = (timing.usage.prompt_tokens / 1_000_000) * pricing.input;
        const outputCost = (timing.usage.completion_tokens / 1_000_000) * pricing.output;
        const totalCost = inputCost + outputCost;

        html += '<div class="timing-row">';
        html += '<span class="timing-label"><strong>Total Cost</strong></span>';
        html += `<span class="timing-value"><strong>$${totalCost.toFixed(4)}</strong></span>`;
        html += '</div>';
        html += '<div class="timing-row small">';
        html += '<span class="timing-label">Prompt Tokens</span>';
        html += `<span class="timing-value">${timing.usage.prompt_tokens.toLocaleString()} ($${inputCost.toFixed(4)})</span>`;
        html += '</div>';
        html += '<div class="timing-row small">';
        html += '<span class="timing-label">Completion Tokens</span>';
        html += `<span class="timing-value">${timing.usage.completion_tokens.toLocaleString()} ($${outputCost.toFixed(4)})</span>`;
        html += '</div>';
        html += '<div class="timing-row small">';
        html += '<span class="timing-label">Total Tokens</span>';
        html += `<span class="timing-value">${timing.usage.total_tokens.toLocaleString()}</span>`;
        html += '</div>';
        html += '<div class="cost-note">* Actual usage from OpenAI API</div>';
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
