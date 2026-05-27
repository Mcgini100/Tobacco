/* ═══════════════════════════════════════════════════════════════
   ChiGwarada — Tobacco Leaf Disease Detection
   Client-side application logic (vanilla JS, no frameworks)
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ──────────────── Internationalization Dictionary ────────────────
const I18N = {
  en: {
    tagline:             'AI-Powered Tobacco Leaf Disease Detection',
    tabUpload:           '📷 Upload Image',
    tabDescribe:         '💬 Describe Symptoms',
    dropText:            'Drag & drop an image here, or click to browse',
    dropHint:            'Supports JPG, PNG, WEBP — Max 10 MB',
    btnCamera:           '📱 Take Photo',
    textareaPlaceholder: 'Describe the symptoms you see on the tobacco leaf… e.g., brown spots, curling edges, yellowing…',
    voiceLabel:          'Voice',
    listening:           'Listening…',
    btnSubmit:           '🔍 Diagnose',
    diseaseDetected:     'Disease Detected',
    confidence:          'Confidence',
    recommendations:     '📋 Recommendations',
    healthy:             'Healthy',
    processing:          'Processing…',
    errorFile:           'Please select a valid image file (JPG, PNG, or WEBP), under 10 MB.',
    errorText:           'Please describe the symptoms (at least 10 characters).',
    errorNetwork:        'Network error. Please check your connection and try again.',
    errorTimeout:        'Request timed out. The server may be busy — please try again.',
    errorRate:           'Too many requests. Please wait a moment before trying again.',
    errorGeneric:        'Something went wrong. Please try again.',
    rateRemaining:       'requests remaining today',
    footerBuilt:         'Built with',
    footerBy:            'by',
    footerUni:           'University Final Year Project',
    voiceNotSupported:   'Voice input is not supported in this browser. Try Chrome or Edge.',
    severity_healthy:    'Healthy',
    severity_low:        'Low',
    severity_moderate:   'Moderate',
    severity_severe:     'Severe',
  },
  sn: {
    tagline:             'Kuongorora Chirwere cheMashizha eFodya neAI',
    tabUpload:           '📷 Tumira Mufananidzo',
    tabDescribe:         '💬 Tsanangura Zviratidzo',
    dropText:            'Dhonzai mufananidzo pano, kana dzvanya kuti mutsvage',
    dropHint:            'Inobvuma JPG, PNG, WEBP — Yakanyanya 10 MB',
    btnCamera:           '📱 Torai Mufananidzo',
    textareaPlaceholder: 'Tsanangurai zviratidzo zvamuri kuona pashizha refodya… semuenzaniso, mavara akasviba, mapetero akakombama, kuyerowa…',
    voiceLabel:          'Inzwi',
    listening:           'Ndiri kuteerera…',
    btnSubmit:           '🔍 Ongorora',
    diseaseDetected:     'Chirwere Chawanikwa',
    confidence:          'Chivimbo',
    recommendations:     '📋 Mazano',
    healthy:             'Yakagwinya',
    processing:          'Ndiri kushanda…',
    errorFile:           'Ndapota sarudzai mufananidzo wakakodzera (JPG, PNG, kana WEBP), uri pasi pe10 MB.',
    errorText:           'Ndapota tsanangurai zviratidzo (okunyanya mavara 10).',
    errorNetwork:        'Dambudziko reNetwork. Ndapota taridzai kusunganidzwa kwenyu mondoedza zvakare.',
    errorTimeout:        'Chikumbiro chazopera nguva. Server inogona kunge yakabatikana — ndapota edzai zvakare.',
    errorRate:           'Zvikumbiro zvizhinji. Ndapota mirai zvishomanana musati maedza zvakare.',
    errorGeneric:        'Chimwe chinhu hachina kuenda zvakanaka. Ndapota edzai zvakare.',
    rateRemaining:       'zvikumbiro zvasara nhasi',
    footerBuilt:         'Yakavakwa ne',
    footerBy:            'na',
    footerUni:           'Chirongwa cheGore Rekupedzisira paYunivhesiti',
    voiceNotSupported:   'Kupinda nenzwi hakutsigiwe mubrowser ino. Edzai Chrome kana Edge.',
    severity_healthy:    'Yakagwinya',
    severity_low:        'Shoma',
    severity_moderate:   'Pakati',
    severity_severe:     'Yakanyanya',
  }
};

// ──────────────── State ────────────────
const state = {
  language:      localStorage.getItem('cg_lang') || 'en',
  mode:          'upload', // 'upload' | 'describe'
  selectedFile:  null,
  isProcessing:  false,
  isRecording:   false,
  recognition:   null,
};

// ──────────────── DOM References ────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
  // Language
  btnLangEn:        $('#btn-lang-en'),
  btnLangSn:        $('#btn-lang-sn'),
  // Tabs
  tabUpload:        $('#tab-upload'),
  tabDescribe:      $('#tab-describe'),
  panelUpload:      $('#panel-upload'),
  panelDescribe:    $('#panel-describe'),
  // Upload
  dropZone:         $('#drop-zone'),
  fileInput:        $('#file-input'),
  cameraInput:      $('#camera-input'),
  btnCamera:        $('#btn-camera'),
  previewContainer: $('#preview-container'),
  imagePreview:     $('#image-preview'),
  btnRemoveImage:   $('#btn-remove-image'),
  fileName:         $('#file-name'),
  // Describe
  symptomText:      $('#symptom-text'),
  btnVoice:         $('#btn-voice'),
  charCounter:      $('#char-counter'),
  voiceIndicator:   $('#voice-indicator'),
  voiceStatus:      $('#voice-status'),
  // Submit
  btnSubmit:        $('#btn-submit'),
  submitText:       $('#submit-text'),
  submitSpinner:    $('#submit-spinner'),
  rateInfo:         $('#rate-info'),
  // Feedback
  errorMessage:     $('#error-message'),
  loadingSkeleton:  $('#loading-skeleton'),
  // Results
  resultsSection:   $('#results-section'),
  resultsCard:      $('#results-card'),
  resultsIcon:      $('#results-icon'),
  resultsTitle:     $('#results-title'),
  diseaseName:      $('#disease-name'),
  severityBadge:    $('#severity-badge'),
  confidenceLabel:  $('#confidence-label'),
  confidenceValue:  $('#confidence-value'),
  confidenceBar:    $('#confidence-bar'),
  descEn:           $('#desc-en'),
  descSn:           $('#desc-sn'),
  recTitle:         $('#rec-title'),
  recListEn:        $('#rec-list-en'),
  recListSn:        $('#rec-list-sn'),
};

// ──────────────── Constants ────────────────
const MAX_FILE_SIZE    = 10 * 1024 * 1024; // 10 MB
const MAX_TEXT_LENGTH  = 500;
const ALLOWED_TYPES    = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
const API_TIMEOUT      = 30_000;           // 30 seconds
const RATE_LIMIT_MAX   = 50;               // Max requests per session
const DEBOUNCE_MS      = 1500;

// ═══════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', init);

function init() {
  applyLanguage(state.language);
  bindLanguageToggle();
  bindTabs();
  bindDropZone();
  bindFileInputs();
  bindTextarea();
  bindVoice();
  bindSubmit();
  bindRemoveImage();
  updateSubmitState();
  initPWA();
  initAuth();
  bindTTS();
}

// ═══════════════════════════════════════════
// PWA SERVICE WORKER
// ═══════════════════════════════════════════
function initPWA() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
      .then(reg => console.log('Service Worker registered', reg))
      .catch(err => console.error('Service Worker registration failed', err));
  }
}

// ═══════════════════════════════════════════
// AUTHENTICATION
// ═══════════════════════════════════════════
function initAuth() {
  const token = localStorage.getItem('cg_token');
  if (token) {
    $('#auth-modal').classList.add('hidden');
  }

  $('#btn-login').addEventListener('click', async () => {
    const user = $('#auth-username').value;
    const pass = $('#auth-password').value;
    if (!user || !pass) return showAuthError("Enter username and password");
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', user);
      formData.append('password', pass);
      
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");
      
      localStorage.setItem('cg_token', data.access_token);
      $('#auth-modal').classList.add('hidden');
    } catch (err) {
      showAuthError(err.message);
    }
  });

  $('#btn-register').addEventListener('click', async () => {
    const user = $('#auth-username').value;
    const pass = $('#auth-password').value;
    if (!user || !pass) return showAuthError("Enter username and password");
    
    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");
      showAuthError("Registration successful. Please login.", true);
    } catch (err) {
      showAuthError(err.message);
    }
  });
}

function showAuthError(msg, isSuccess = false) {
  const errEl = $('#auth-error');
  errEl.textContent = msg;
  errEl.classList.remove('hidden');
  errEl.style.color = isSuccess ? 'var(--success)' : 'var(--danger)';
  errEl.style.borderColor = isSuccess ? 'var(--success)' : 'var(--danger)';
}

// ═══════════════════════════════════════════
// TEXT-TO-SPEECH (TTS)
// ═══════════════════════════════════════════
function bindTTS() {
  $('#btn-tts').addEventListener('click', () => {
    const textEn = dom.descEn.textContent;
    const textSn = dom.descSn.textContent;
    const recsEn = Array.from(dom.recListEn.querySelectorAll('li')).map(li => li.textContent).join('. ');
    const recsSn = Array.from(dom.recListSn.querySelectorAll('li')).map(li => li.textContent).join('. ');
    
    let textToSpeak = '';
    let lang = 'en-US';
    
    if (state.language === 'sn') {
      textToSpeak = `Chirwere chinofungidzirwa: ${dom.diseaseName.textContent}. ${textSn} Mazano anoti: ${recsSn}`;
      // Shona isn't widely supported natively, but we can attempt to use default voice or es-ES for phonetic match
      lang = 'es-ES'; 
    } else {
      textToSpeak = `Detected Disease: ${dom.diseaseName.textContent}. ${textEn} Recommendations are: ${recsEn}`;
      lang = 'en-US';
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel(); // Stop any ongoing speech
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      utterance.lang = lang;
      utterance.rate = 0.9; // slightly slower
      window.speechSynthesis.speak(utterance);
    } else {
      showError(t('voiceNotSupported'));
    }
  });
}

// ═══════════════════════════════════════════
// LANGUAGE
// ═══════════════════════════════════════════

/** Apply language to all i18n-tagged elements */
function applyLanguage(lang) {
  state.language = lang;
  localStorage.setItem('cg_lang', lang);

  // Update language buttons
  dom.btnLangEn.classList.toggle('active', lang === 'en');
  dom.btnLangSn.classList.toggle('active', lang === 'sn');
  dom.btnLangEn.setAttribute('aria-pressed', lang === 'en');
  dom.btnLangSn.setAttribute('aria-pressed', lang === 'sn');

  // Update html lang attribute
  document.documentElement.lang = lang === 'sn' ? 'sn' : 'en';

  // Update all data-i18n elements
  $$('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (I18N[lang][key]) {
      el.textContent = I18N[lang][key];
    }
  });

  // Update placeholders
  $$('[data-i18n-placeholder]').forEach(el => {
    const key = el.dataset.i18nPlaceholder;
    if (I18N[lang][key]) {
      el.placeholder = I18N[lang][key];
    }
  });
}

function bindLanguageToggle() {
  dom.btnLangEn.addEventListener('click', () => applyLanguage('en'));
  dom.btnLangSn.addEventListener('click', () => applyLanguage('sn'));
}

/** Helper to get a translated string */
function t(key) {
  return I18N[state.language][key] || I18N['en'][key] || key;
}

// ═══════════════════════════════════════════
// TABS
// ═══════════════════════════════════════════

function bindTabs() {
  dom.tabUpload.addEventListener('click', () => switchTab('upload'));
  dom.tabDescribe.addEventListener('click', () => switchTab('describe'));
}

function switchTab(mode) {
  state.mode = mode;

  // Update tab buttons
  dom.tabUpload.classList.toggle('active', mode === 'upload');
  dom.tabDescribe.classList.toggle('active', mode === 'describe');
  dom.tabUpload.setAttribute('aria-selected', mode === 'upload');
  dom.tabDescribe.setAttribute('aria-selected', mode === 'describe');

  // Update panels
  dom.panelUpload.classList.toggle('active', mode === 'upload');
  dom.panelDescribe.classList.toggle('active', mode === 'describe');
  dom.panelUpload.hidden = mode !== 'upload';
  dom.panelDescribe.hidden = mode !== 'describe';

  // Hide results & errors on tab switch
  hideError();
  hideResults();
  updateSubmitState();
}

// ═══════════════════════════════════════════
// DRAG & DROP / FILE UPLOAD
// ═══════════════════════════════════════════

function bindDropZone() {
  const dz = dom.dropZone;

  // Click to browse
  dz.addEventListener('click', () => dom.fileInput.click());
  dz.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      dom.fileInput.click();
    }
  });

  // Drag events
  dz.addEventListener('dragenter', handleDragEnter);
  dz.addEventListener('dragover',  handleDragOver);
  dz.addEventListener('dragleave', handleDragLeave);
  dz.addEventListener('drop',      handleDrop);
}

function handleDragEnter(e) {
  e.preventDefault();
  dom.dropZone.classList.add('drag-over');
}

function handleDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'copy';
  dom.dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
  e.preventDefault();
  // Only remove if we truly left the drop zone
  if (!dom.dropZone.contains(e.relatedTarget)) {
    dom.dropZone.classList.remove('drag-over');
  }
}

function handleDrop(e) {
  e.preventDefault();
  dom.dropZone.classList.remove('drag-over');

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFileSelection(files[0]);
  }
}

function bindFileInputs() {
  dom.fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  dom.cameraInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  dom.btnCamera.addEventListener('click', () => dom.cameraInput.click());
}

function handleFileSelection(file) {
  // Validate type
  if (!ALLOWED_TYPES.includes(file.type)) {
    showError(t('errorFile'));
    return;
  }

  // Validate size
  if (file.size > MAX_FILE_SIZE) {
    showError(t('errorFile'));
    return;
  }

  hideError();
  state.selectedFile = file;

  // Show preview
  const reader = new FileReader();
  reader.onload = (e) => {
    dom.imagePreview.src = e.target.result;
    dom.previewContainer.classList.remove('hidden');
    dom.fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
  };
  reader.readAsDataURL(file);

  updateSubmitState();
}

function bindRemoveImage() {
  dom.btnRemoveImage.addEventListener('click', (e) => {
    e.stopPropagation();
    removeSelectedFile();
  });
}

function removeSelectedFile() {
  state.selectedFile = null;
  dom.imagePreview.src = '';
  dom.previewContainer.classList.add('hidden');
  dom.fileInput.value = '';
  dom.cameraInput.value = '';
  dom.fileName.textContent = '';
  updateSubmitState();
}

/** Format bytes to human-readable string */
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ═══════════════════════════════════════════
// TEXTAREA / DESCRIPTION
// ═══════════════════════════════════════════

function bindTextarea() {
  dom.symptomText.addEventListener('input', () => {
    updateCharCounter();
    updateSubmitState();
  });
  updateCharCounter();
}

function updateCharCounter() {
  const len = dom.symptomText.value.length;
  dom.charCounter.textContent = `${len} / ${MAX_TEXT_LENGTH}`;

  dom.charCounter.classList.remove('near-limit', 'at-limit');
  if (len >= MAX_TEXT_LENGTH) {
    dom.charCounter.classList.add('at-limit');
  } else if (len >= MAX_TEXT_LENGTH * 0.85) {
    dom.charCounter.classList.add('near-limit');
  }
}

// ═══════════════════════════════════════════
// VOICE INPUT (Web Speech API)
// ═══════════════════════════════════════════

function bindVoice() {
  dom.btnVoice.addEventListener('click', toggleVoice);
}

function toggleVoice() {
  if (state.isRecording) {
    stopVoice();
  } else {
    startVoice();
  }
}

function startVoice() {
  // Check browser support
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showError(t('voiceNotSupported'));
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  // Set language — Shona doesn't have a standard BCP-47 code in most browsers,
  // so we use English as the fallback for both
  recognition.lang = state.language === 'sn' ? 'en-US' : 'en-US';

  recognition.onstart = () => {
    state.isRecording = true;
    dom.btnVoice.classList.add('recording');
    dom.voiceIndicator.classList.remove('hidden');
  };

  recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }

    // Only append final results
    if (event.results[event.results.length - 1].isFinal) {
      const current = dom.symptomText.value;
      const separator = current && !current.endsWith(' ') ? ' ' : '';
      const newText = (current + separator + transcript).slice(0, MAX_TEXT_LENGTH);
      dom.symptomText.value = newText;
      updateCharCounter();
      updateSubmitState();
    }
  };

  recognition.onerror = (event) => {
    console.warn('Speech recognition error:', event.error);
    stopVoice();
    if (event.error === 'not-allowed') {
      showError(t('voiceNotSupported'));
    }
  };

  recognition.onend = () => {
    stopVoice();
  };

  try {
    recognition.start();
    state.recognition = recognition;

    // Auto-stop after 30 seconds
    setTimeout(() => {
      if (state.isRecording) {
        stopVoice();
      }
    }, 30_000);
  } catch (err) {
    console.error('Failed to start speech recognition:', err);
    showError(t('voiceNotSupported'));
  }
}

function stopVoice() {
  state.isRecording = false;
  dom.btnVoice.classList.remove('recording');
  dom.voiceIndicator.classList.add('hidden');

  if (state.recognition) {
    try {
      state.recognition.stop();
    } catch (_) { /* ignore */ }
    state.recognition = null;
  }
}

// ═══════════════════════════════════════════
// SUBMIT / API
// ═══════════════════════════════════════════

/** Enable/disable submit button based on current state */
function updateSubmitState() {
  let ready = false;
  if (state.mode === 'upload') {
    ready = !!state.selectedFile;
  } else {
    ready = dom.symptomText.value.trim().length >= 10;
  }
  dom.btnSubmit.disabled = !ready || state.isProcessing;
}

let lastSubmitTime = 0;

function bindSubmit() {
  dom.btnSubmit.addEventListener('click', handleSubmit);
}

async function handleSubmit() {
  // Debounce — prevent rapid double-clicks
  const now = Date.now();
  if (now - lastSubmitTime < DEBOUNCE_MS) return;
  lastSubmitTime = now;

  // Rate limit check
  if (!checkRateLimit()) {
    showError(t('errorRate'));
    return;
  }

  hideError();
  hideResults();

  if (state.mode === 'upload') {
    await submitImage();
  } else {
    await submitDescription();
  }
}

async function submitImage() {
  if (!state.selectedFile) {
    showError(t('errorFile'));
    return;
  }

  setProcessing(true);

  const formData = new FormData();
  formData.append('file', state.selectedFile);

  try {
    const data = await apiCall('/api/diagnose', {
      method: 'POST',
      body: formData,
    });
    incrementRateCount();
    renderResults(data);
  } catch (err) {
    handleApiError(err);
  } finally {
    setProcessing(false);
  }
}

async function submitDescription() {
  const text = dom.symptomText.value.trim();
  if (text.length < 10) {
    showError(t('errorText'));
    return;
  }

  setProcessing(true);

  try {
    const data = await apiCall('/api/describe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        language: state.language,
      }),
    });
    incrementRateCount();
    renderResults(data);
  } catch (err) {
    handleApiError(err);
  } finally {
    setProcessing(false);
  }
}

/** Generic API call with timeout */
async function apiCall(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const token = localStorage.getItem('cg_token');
    const headers = options.headers || {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(url, {
      ...options,
      headers: headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.status === 429) {
      throw new ApiError('rate_limit', t('errorRate'));
    }

    if (!response.ok) {
      const errorBody = await response.text().catch(() => '');
      throw new ApiError('http', `Server error (${response.status}): ${errorBody || 'Unknown error'}`);
    }

    const data = await response.json();

    if (!data.success) {
      throw new ApiError('api', data.message || t('errorGeneric'));
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);

    if (err instanceof ApiError) throw err;

    if (err.name === 'AbortError') {
      throw new ApiError('timeout', t('errorTimeout'));
    }

    throw new ApiError('network', t('errorNetwork'));
  }
}

/** Custom error class for API errors */
class ApiError extends Error {
  constructor(type, message) {
    super(message);
    this.type = type;
  }
}

function handleApiError(err) {
  console.error('API Error:', err);
  showError(err.message || t('errorGeneric'));
}

// ═══════════════════════════════════════════
// PROCESSING STATE
// ═══════════════════════════════════════════

function setProcessing(active) {
  state.isProcessing = active;

  dom.btnSubmit.disabled = active;
  dom.submitSpinner.classList.toggle('hidden', !active);
  dom.submitText.textContent = active ? t('processing') : t('btnSubmit');
  dom.loadingSkeleton.classList.toggle('hidden', !active);

  if (active) {
    hideResults();
  }
}

// ═══════════════════════════════════════════
// RESULTS RENDERING
// ═══════════════════════════════════════════

function renderResults(data) {
  // Extract fields from the backend's nested response structure
  const diagnosis = data.diagnosis || {};
  const prediction = data.prediction || {};
  
  const {
    disease_name_en: disease = 'Unknown',
    description_en = '',
    description_sn = '',
    recommendations_en = [],
    recommendations_sn = [],
    confidence_note = '',
    severity = 'moderate',
  } = diagnosis;

  // For image uploads, confidence comes from prediction. For text, it might be 0.
  const confidence = (prediction.confidence || 0) * 100;

  // Determine if healthy
  const isHealthy = disease.toLowerCase().includes('healthy') ||
                    disease.toLowerCase().includes('yakagwinya');

  // Icon
  dom.resultsIcon.textContent = isHealthy ? '✅' : '🔬';

  // Icon wrapper color
  const iconWrapper = dom.resultsIcon.parentElement;
  iconWrapper.style.background = isHealthy
    ? 'rgba(34, 197, 94, 0.15)'
    : severity === 'severe'
      ? 'rgba(239, 68, 68, 0.15)'
      : 'rgba(245, 158, 11, 0.15)';

  // Title & name
  dom.resultsTitle.textContent = isHealthy ? t('healthy') : t('diseaseDetected');
  dom.diseaseName.textContent = disease;

  // Severity badge
  const sevNorm = normalizeSeverity(severity, isHealthy);
  dom.severityBadge.textContent = t(`severity_${sevNorm}`);
  dom.severityBadge.className = `severity-badge ${sevNorm}`;

  // Card accent class
  dom.resultsCard.className = 'results-card';
  dom.resultsCard.classList.add(`severity-${sevNorm}`);

  // Confidence bar
  const confPct = Math.min(100, Math.max(0, confidence));
  dom.confidenceValue.textContent = confPct.toFixed(1) + '%';

  // Animate confidence bar
  dom.confidenceBar.style.width = '0%';
  dom.confidenceBar.className = 'confidence-fill';
  if (confPct >= 80) dom.confidenceBar.classList.add('high');
  else if (confPct >= 50) dom.confidenceBar.classList.add('medium');
  else dom.confidenceBar.classList.add('low');

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      dom.confidenceBar.style.width = confPct + '%';
    });
  });

  // Descriptions
  const confNoteHtml = confidence_note ? `<br><br><strong style="color: #ef4444; padding: 10px; background: rgba(239, 68, 68, 0.1); border-radius: 8px; display: inline-block; border-left: 4px solid #ef4444;">⚠️ ${confidence_note}</strong>` : '';
  dom.descEn.innerHTML = (description_en || '—') + confNoteHtml;
  dom.descSn.innerHTML = (description_sn || '—') + confNoteHtml;

  // Recommendations
  dom.recListEn.innerHTML = '';
  dom.recListSn.innerHTML = '';

  (recommendations_en || []).forEach(rec => {
    const li = document.createElement('li');
    li.textContent = rec;
    dom.recListEn.appendChild(li);
  });

  (recommendations_sn || []).forEach(rec => {
    const li = document.createElement('li');
    li.textContent = rec;
    dom.recListSn.appendChild(li);
  });

  // Show results
  dom.resultsSection.classList.remove('hidden');

  // Smooth scroll to results
  setTimeout(() => {
    dom.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
}

function normalizeSeverity(severity, isHealthy) {
  if (isHealthy) return 'healthy';
  const s = (severity || '').toLowerCase();
  if (s === 'severe' || s === 'high') return 'severe';
  if (s === 'moderate' || s === 'medium') return 'moderate';
  if (s === 'low' || s === 'mild') return 'low';
  return 'moderate'; // default
}

function hideResults() {
  dom.resultsSection.classList.add('hidden');
}

// ═══════════════════════════════════════════
// ERROR DISPLAY
// ═══════════════════════════════════════════

function showError(message) {
  dom.errorMessage.textContent = message;
  dom.errorMessage.classList.remove('hidden');

  // Auto-hide after 8 seconds
  setTimeout(() => hideError(), 8000);
}

function hideError() {
  dom.errorMessage.classList.add('hidden');
}

// ═══════════════════════════════════════════
// RATE LIMITING (Client-side tracking)
// ═══════════════════════════════════════════

function getRateCount() {
  const stored = sessionStorage.getItem('cg_rate');
  if (!stored) return 0;
  try {
    const { count, date } = JSON.parse(stored);
    // Reset if it's a new day
    if (date !== new Date().toDateString()) return 0;
    return count;
  } catch {
    return 0;
  }
}

function incrementRateCount() {
  const count = getRateCount() + 1;
  sessionStorage.setItem('cg_rate', JSON.stringify({
    count,
    date: new Date().toDateString(),
  }));
  updateRateDisplay(count);
}

function checkRateLimit() {
  const count = getRateCount();
  if (count >= RATE_LIMIT_MAX) {
    return false;
  }
  updateRateDisplay(count);
  return true;
}

function updateRateDisplay(count) {
  const remaining = Math.max(0, RATE_LIMIT_MAX - count);
  if (remaining <= 10) {
    dom.rateInfo.textContent = `${remaining} ${t('rateRemaining')}`;
    dom.rateInfo.classList.remove('hidden');
  } else {
    dom.rateInfo.classList.add('hidden');
  }
}
