/* ═══════════════════════════════════════════════════════════════
   AgriVision — Client-side application logic
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ──────────────── Internationalization Dictionary ────────────────
const I18N = {
  en: {
    homeWelcome:         'Welcome to AgriVision',
    homeSubtitle:        'Your Smart Tobacco Farming Assistant.',
    homeDiagnoseDesc:    'Scan leaves to detect diseases.',
    homeGuideDesc:       'Learn about tobacco diseases.',
    homeMarketDesc:      'Get updates on weather and prices.',
    navHome:             'Home',
    navDiagnose:         'Diagnose',
    navGuide:            'Guide',
    navMarket:           'Market',
    tabUpload:           'Upload Image',
    tabDescribe:         'Describe Symptoms',
    dropText:            'Drag & drop an image here',
    dropHint:            'Supports JPG, PNG, WEBP — Max 10 MB',
    btnCamera:           'Take Photo',
    textareaPlaceholder: 'Describe symptoms... e.g., brown spots...',
    voiceLabel:          'Voice',
    listening:           'Listening...',
    btnSubmit:           'Diagnose',
    diseaseDetected:     'Disease Detected',
    confidence:          'Confidence',
    recommendations:     'Recommendations',
    healthy:             'Healthy',
    processing:          'Processing...',
    errorFile:           'Please select a valid image file (JPG, PNG, or WEBP), under 10 MB.',
    errorText:           'Please describe the symptoms (at least 10 characters).',
    errorNetwork:        'Network error. Please check your connection.',
    errorGeneric:        'Something went wrong. Please try again.',
    voiceNotSupported:   'Voice input is not supported in this browser.',
    guideTitle:          'Tobacco Disease Guide',
    guideSubtitle:       'Common diseases affecting tobacco crops, identification, and prevention strategies.',
    weatherTitle:        'Market & Weather Updates',
    guideBrownSpotTitle: 'Alternaria Alternata (Brown Spot)',
    guideBrownSpotDesc:  'Brown spot appears as circular spots on the lower leaves, gradually moving upwards. It is favored by warm, humid conditions and can cause significant yield loss if not managed.',
    guideMgmtTitle:      'Management',
    guideBrownSpotTip1:  'Early reaping to remove infected lower leaves.',
    guideBrownSpotTip2:  'Proper curing and avoiding excessive nitrogen fertilizer.',
    guideBrownSpotTip3:  'Apply registered fungicides when symptoms first appear.',
    guideFrogEyeTitle:   'Cercospora Nicotianae (Frog Eye Spot)',
    guideFrogEyeDesc:    'Characterized by small, circular spots with white or light tan centers resembling frog eyes. It commonly occurs in wet weather and can lower leaf quality.',
    guideFrogEyeTip1:    'Maintain strict seedbed hygiene.',
    guideFrogEyeTip2:    'Destroy crop residues after harvest.',
    guideFrogEyeTip3:    'Ensure proper plant spacing for air circulation.',
    guideTMVTitle:       'Tobacco Mosaic Virus (TMV)',
    guideTMVDesc:        'Causes mottling and discoloration of leaves (a mosaic pattern). It is highly contagious and usually spread through mechanical transmission (hands, tools).',
    guideTMVTip1:        'Wash hands thoroughly with soap and water before handling plants.',
    guideTMVTip2:        'Do not smoke or use tobacco products while in the field.',
    guideTMVTip3:        'Use TMV-resistant tobacco varieties if available.',
    guideAngularTitle:   'Angular Leaf Spot (Pseudomonas syringae)',
    guideAngularDesc:    'A bacterial disease causing dark, angular spots on leaves, often surrounded by a yellow halo. Spread is favored by driving rain and wind.',
    guideAngularTip1:    'Avoid working in the field when plants are wet.',
    guideAngularTip2:    'Rotate crops and bury or burn infected stalks.',
    guideAngularTip3:    'Apply copper-based bactericides preventatively in high-risk areas.'
  },
  sn: {
    homeWelcome:         'Titambirei kuAgriVision',
    homeSubtitle:        'Mubatsiri Wenyu weKuvakisa Fodya.',
    homeDiagnoseDesc:    'Ongororai mashizha kutsvaga zvirwere.',
    homeGuideDesc:       'Dzidzai nezvezvirwere zvekufodya.',
    homeMarketDesc:      'Wana ruzivo rwemamiriro ekunze nemitengo.',
    navHome:             'Peji Huru',
    navDiagnose:         'Ongorora',
    navGuide:            'Nhungamiro',
    navMarket:           'Musika',
    tabUpload:           'Tumira Mufananidzo',
    tabDescribe:         'Tsanangura Zviratidzo',
    dropText:            'Dhonzai mufananidzo pano',
    dropHint:            'Inobvuma JPG, PNG, WEBP — Yakanyanya 10 MB',
    btnCamera:           'Torai Mufananidzo',
    textareaPlaceholder: 'Tsanangurai zviratidzo... semuenzaniso, mavara...',
    voiceLabel:          'Inzwi',
    listening:           'Ndiri kuteerera...',
    btnSubmit:           'Ongorora',
    diseaseDetected:     'Chirwere Chawanikwa',
    confidence:          'Chivimbo',
    recommendations:     'Mazano',
    healthy:             'Yakagwinya',
    processing:          'Ndiri kushanda...',
    errorFile:           'Ndapota sarudzai mufananidzo wakakodzera.',
    errorText:           'Ndapota tsanangurai zviratidzo zvakakwana.',
    errorNetwork:        'Dambudziko reNetwork.',
    errorGeneric:        'Pane dambudziko. Ndapota edzai zvakare.',
    voiceNotSupported:   'Kupinda nenzwi hakutsigiwe mubrowser ino.',
    guideTitle:          'Nhungamiro yeZvirwere zveFodya',
    guideSubtitle:       'Zvirwere zvakajairika zvinokanganisa fodya.',
    weatherTitle:        'Mamiriro Ekunze & Musika',
    guideBrownSpotTitle: 'Alternaria Alternata (Zvirwere Zvemaziso eShava)',
    guideBrownSpotDesc:  'Zvirwere zvemaziso eshava zvinoonekwa semavara akatenderera pamashizha epasi, zvichikwira kumusoro. Zvinofarirwa nemamiriro ekunze anodziya, ane hunyoro uye zvinogona kuderedza goho zvakanyanya kana zvikasagadziriswa.',
    guideMgmtTitle:      'Kudzivirira nekurapa',
    guideBrownSpotTip1:  'Kukohwa nekukurumidza kuti ubvise mashizha epasi ane chirwere.',
    guideBrownSpotTip2:  'Kurapa zvakanaka uye kudzivisa fetireza yenitrogen yakawandisa.',
    guideBrownSpotTip3:  'Shandisa mishonga inobvumirwa kana zviratidzo zvotanga kuonekwa.',
    guideFrogEyeTitle:   'Cercospora Nicotianae (Ziso reDatya)',
    guideFrogEyeDesc:    'Chinozivikanwa nemavara madiki akatenderera ane chena kana chiedza tan center akafanana nemeso edatya. Zvinowanzokanganisa munguva yekunaya kwemvura uye zvinogona kuderedza kunaka kwemashizha.',
    guideFrogEyeTip1:    'Chengetedza hutsanana hwepamusoro pamibhedha yembeu.',
    guideFrogEyeTip2:    'Kupisa zvisaririra zvezvirimwa mushure mekukohwa.',
    guideFrogEyeTip3:    'Iva nechokwadi chekusiya nzvimbo yakakwana pakati pemiti kuti mhepo ifambe zvakanaka.',
    guideTMVTitle:       'Hutachiwana hweFodya (TMV)',
    guideTMVDesc:        'Inokonzera kushanduka kwemavara emashizha (chimiro che mosaic). Inotapukira zvikuru uye inowanzoparadzirwa kuburikidza nemaoko kana zvombo zvekushandisa.',
    guideTMVTip1:        'Geza maoko ako zvakanaka nesipo nemvura usati wabata zvirimwa.',
    guideTMVTip2:        'Usaputa kana kushandisa fodya paunenge uri mumunda.',
    guideTMVTip3:        'Shandisa mhando dzefodya dzisingabatirwe neTMV kana dziripo.',
    guideAngularTitle:   'Chirwere cheMashizha AneMakona (Angular Leaf Spot)',
    guideAngularDesc:    'Chirwere chebhakitiriya chinokonzera mavara matema, ane makona pamashizha, anowanzotenderedzwa nehalo yellow. Kupararira kunofarirwa nemvura inonaya nemhepo.',
    guideAngularTip1:    'Usashanda mumunda kana zvirimwa zvakanyorova.',
    guideAngularTip2:    'Chinja zvirimwa zvaunodyara woviga kana kupisa madzinde ane chirwere.',
    guideAngularTip3:    'Shandisa mishonga inobva pamhangura kuchengetedza munzvimbo dzine njodzi huru.'
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
  // Navigation
  navBtns:          $$('.nav-btn'),
  pageSections:     $$('.page-section'),
  homeCards:        $$('.home-card'),

  // Language
  btnLangEn:        $('#btn-lang-en'),
  btnLangSn:        $('#btn-lang-sn'),

  // Global Voice
  btnGlobalVoice:   $('#btn-global-voice'),
  globalVoiceInd:   $('#global-voice-indicator'),
  globalVoiceStatus:$('#global-voice-status'),

  // Tabs (Diagnose)
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

  // Submit
  btnSubmit:        $('#btn-submit'),
  submitText:       $('#submit-text'),
  submitSpinner:    $('#submit-spinner'),

  // Feedback
  errorMessage:     $('#error-message'),
  loadingSkeleton:  $('#loading-skeleton'),

  // Results
  resultsSection:   $('#results-section'),
  resultsCard:      $('#results-card'),
  diseaseName:      $('#disease-name'),
  severityBadge:    $('#severity-badge'),
  confidenceValue:  $('#confidence-value'),
  confidenceBar:    $('#confidence-bar'),
  descEn:           $('#desc-en'),
  descSn:           $('#desc-sn'),
  recListEn:        $('#rec-list-en'),
  recListSn:        $('#rec-list-sn'),
  btnTts:           $('#btn-tts')
};

// ═══════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  applyLanguage(state.language);
  bindLanguageToggle();
  bindTabs();
  bindDropZone();
  bindFileInputs();
  bindTextarea();
  bindVoice();
  bindGlobalVoice();
  bindSubmit();
  bindRemoveImage();
  bindTTS();
  initAuth();
  fetchWeather();
  setMarketDate();

  // Register Service Worker for PWA
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('[Service Worker] Registered with scope:', registration.scope);
      })
      .catch((error) => {
        console.error('[Service Worker] Registration failed:', error);
      });
  }
});

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
// NAVIGATION
// ═══════════════════════════════════════════
function initNavigation() {
  window.addEventListener('hashchange', handleHashChange);
  
  // Set initial state based on hash or default to home
  handleHashChange();

  dom.navBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const target = e.currentTarget.getAttribute('data-target');
      window.location.hash = target;
    });
  });

  dom.homeCards.forEach(card => {
    card.addEventListener('click', (e) => {
      e.preventDefault();
      const target = e.currentTarget.getAttribute('data-target');
      window.location.hash = target;
    });
  });
}

function handleHashChange() {
  let hash = window.location.hash.substring(1);
  if (!hash || !document.getElementById(hash)) {
    hash = 'page-home';
    history.replaceState(null, null, '#' + hash);
  }
  navigateTo(hash);
}

function navigateTo(pageId) {
  // Update sections
  dom.pageSections.forEach(sec => sec.classList.remove('active', 'hidden'));
  dom.pageSections.forEach(sec => {
    if (sec.id !== pageId) {
      sec.classList.add('hidden');
    } else {
      sec.classList.add('active');
    }
  });

  // Update nav buttons
  dom.navBtns.forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.querySelector(`.nav-btn[data-target="${pageId}"]`);
  if (activeBtn) activeBtn.classList.add('active');
  
  window.scrollTo({ top: 0, behavior: 'smooth' });
}


// ═══════════════════════════════════════════
// LANGUAGE
// ═══════════════════════════════════════════
function applyLanguage(lang) {
  state.language = lang;
  localStorage.setItem('cg_lang', lang);

  dom.btnLangEn.classList.toggle('active', lang === 'en');
  dom.btnLangSn.classList.toggle('active', lang === 'sn');

  $$('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (I18N[lang][key]) el.textContent = I18N[lang][key];
  });

  $$('[data-i18n-placeholder]').forEach(el => {
    const key = el.dataset.i18nPlaceholder;
    if (I18N[lang][key]) el.placeholder = I18N[lang][key];
  });

  // Toggle English / Shona blocks in results
  if (dom.descEn && dom.descSn) {
    const enBlock = dom.descEn.closest('.desc-block');
    const snBlock = dom.descSn.closest('.desc-block');
    const recHeadingSn = document.querySelector('.rec-heading-sn');
    const recTitleEn = document.getElementById('rec-title');

    if (lang === 'en') {
      if (enBlock) enBlock.style.display = 'block';
      if (snBlock) snBlock.style.display = 'none';
      if (dom.recListEn) dom.recListEn.style.display = 'block';
      if (dom.recListSn) dom.recListSn.style.display = 'none';
      if (recHeadingSn) recHeadingSn.style.display = 'none';
      if (recTitleEn) recTitleEn.style.display = 'block';
    } else {
      if (enBlock) enBlock.style.display = 'none';
      if (snBlock) snBlock.style.display = 'block';
      if (dom.recListEn) dom.recListEn.style.display = 'none';
      if (dom.recListSn) dom.recListSn.style.display = 'block';
      if (recHeadingSn) recHeadingSn.style.display = 'block';
      if (recTitleEn) recTitleEn.style.display = 'none';
    }
  }
}

function bindLanguageToggle() {
  dom.btnLangEn.addEventListener('click', () => applyLanguage('en'));
  dom.btnLangSn.addEventListener('click', () => applyLanguage('sn'));
}

function t(key) {
  return I18N[state.language][key] || I18N['en'][key] || key;
}

// ═══════════════════════════════════════════
// TABS (Diagnose)
// ═══════════════════════════════════════════
function bindTabs() {
  dom.tabUpload.addEventListener('click', () => switchTab('upload'));
  dom.tabDescribe.addEventListener('click', () => switchTab('describe'));
}

function switchTab(mode) {
  state.mode = mode;
  dom.tabUpload.classList.toggle('active', mode === 'upload');
  dom.tabDescribe.classList.toggle('active', mode === 'describe');
  dom.panelUpload.hidden = mode !== 'upload';
  dom.panelDescribe.hidden = mode !== 'describe';
  dom.panelUpload.classList.toggle('active', mode === 'upload');
  dom.panelDescribe.classList.toggle('active', mode === 'describe');

  hideError();
  hideResults();
  updateSubmitState();
}

// ═══════════════════════════════════════════
// FILE UPLOAD & PREVIEW
// ═══════════════════════════════════════════
function bindDropZone() {
  const dz = dom.dropZone;
  dz.addEventListener('click', () => dom.fileInput.click());
  dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.style.borderColor = 'var(--accent-light)'; });
  dz.addEventListener('dragleave', (e) => { e.preventDefault(); dz.style.borderColor = 'var(--accent-border)'; });
  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.style.borderColor = 'var(--accent-border)';
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });
}

function bindFileInputs() {
  dom.fileInput.addEventListener('change', (e) => { if(e.target.files.length) handleFile(e.target.files[0]); });
  dom.cameraInput.addEventListener('change', (e) => { if(e.target.files.length) handleFile(e.target.files[0]); });
  dom.btnCamera.addEventListener('click', () => dom.cameraInput.click());
}

function handleFile(file) {
  const ALLOWED = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
  if (!ALLOWED.includes(file.type) || file.size > 10 * 1024 * 1024) {
    showError(t('errorFile'));
    return;
  }
  
  hideError();
  state.selectedFile = file;
  
  const reader = new FileReader();
  reader.onload = (e) => {
    dom.imagePreview.src = e.target.result;
    dom.previewContainer.classList.remove('hidden');
    dom.fileName.textContent = file.name;
  };
  reader.readAsDataURL(file);
  updateSubmitState();
}

function bindRemoveImage() {
  dom.btnRemoveImage.addEventListener('click', (e) => {
    e.stopPropagation();
    state.selectedFile = null;
    dom.imagePreview.src = '';
    dom.previewContainer.classList.add('hidden');
    dom.fileInput.value = '';
    updateSubmitState();
  });
}

// ═══════════════════════════════════════════
// TEXTAREA
// ═══════════════════════════════════════════
function bindTextarea() {
  dom.symptomText.addEventListener('input', () => {
    dom.charCounter.textContent = `${dom.symptomText.value.length} / 500`;
    updateSubmitState();
  });
}

// ═══════════════════════════════════════════
// VOICE INPUT
// ═══════════════════════════════════════════
function bindVoice() {
  dom.btnVoice.addEventListener('click', () => toggleVoice(false));
}

function bindGlobalVoice() {
  dom.btnGlobalVoice.addEventListener('click', () => {
    if (state.isRecording) {
      stopVoice();
    } else {
      window.location.hash = 'page-diagnose';
      switchTab('describe');
      toggleVoice(true);
    }
  });
}

function toggleVoice(isGlobalTrigger = false) {
  if (state.isRecording) {
    stopVoice();
  } else {
    startVoice(isGlobalTrigger);
  }
}

function startVoice(isGlobalTrigger) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return showError(t('voiceNotSupported'));

  const recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = state.language === 'sn' ? 'sn-ZW' : 'en-US';

  recognition.onstart = () => {
    state.isRecording = true;
    dom.btnVoice.classList.add('recording');
    dom.btnGlobalVoice.classList.add('recording');
    dom.voiceIndicator.classList.remove('hidden');
    dom.globalVoiceInd.classList.remove('hidden');
  };

  recognition.onresult = (e) => {
    let transcript = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      transcript += e.results[i][0].transcript;
    }
    if (e.results[e.results.length - 1].isFinal) {
      const cur = dom.symptomText.value;
      dom.symptomText.value = (cur + (cur?' ':'') + transcript).slice(0, 500);
      dom.charCounter.textContent = `${dom.symptomText.value.length} / 500`;
      updateSubmitState();
    }
  };

  recognition.onerror = () => stopVoice();
  recognition.onend = () => stopVoice();

  try {
    state.isRecording = true;
    recognition.start();
    state.recognition = recognition;
    setTimeout(() => { if(state.isRecording) stopVoice(); }, 30000);
  } catch(err) {
    stopVoice();
  }
}

function stopVoice() {
  state.isRecording = false;
  dom.btnVoice.classList.remove('recording');
  dom.btnGlobalVoice.classList.remove('recording');
  dom.voiceIndicator.classList.add('hidden');
  dom.globalVoiceInd.classList.add('hidden');
  if (state.recognition) {
    try { state.recognition.stop(); } catch(e){}
    state.recognition = null;
  }
}

// ═══════════════════════════════════════════
// SUBMISSION
// ═══════════════════════════════════════════
function updateSubmitState() {
  let ready = state.mode === 'upload' ? !!state.selectedFile : dom.symptomText.value.trim().length >= 10;
  dom.btnSubmit.disabled = !ready || state.isProcessing;
}

function bindSubmit() {
  dom.btnSubmit.addEventListener('click', async () => {
    hideError();
    hideResults();
    setProcessing(true);

    try {
      const token = localStorage.getItem('cg_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      let res, data;

      if (state.mode === 'upload') {
        const formData = new FormData();
        formData.append('file', state.selectedFile);
        res = await fetch('/api/diagnose', { method: 'POST', headers, body: formData });
      } else {
        headers['Content-Type'] = 'application/json';
        res = await fetch('/api/describe', {
          method: 'POST',
          headers,
          body: JSON.stringify({ text: dom.symptomText.value.trim(), language: state.language })
        });
      }

      data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.message || t('errorGeneric'));
      if (!data.success) throw new Error(data.message || t('errorGeneric'));

      renderResults(data);
    } catch (err) {
      showError(err.message);
    } finally {
      setProcessing(false);
    }
  });
}

function setProcessing(isProc) {
  state.isProcessing = isProc;
  dom.btnSubmit.disabled = isProc;
  dom.submitSpinner.classList.toggle('hidden', !isProc);
  dom.submitText.textContent = isProc ? t('processing') : t('btnSubmit');
  dom.loadingSkeleton.classList.toggle('hidden', !isProc);
}

// ═══════════════════════════════════════════
// RESULTS & TTS
// ═══════════════════════════════════════════
function renderResults(data) {
  const diagnosis = data.diagnosis || {};
  const prediction = data.prediction || {};

  dom.diseaseName.textContent = diagnosis.disease_name_en || 'Unknown';
  
  const isHealthy = (diagnosis.disease_name_en || '').toLowerCase().includes('healthy');
  const severity = isHealthy ? 'healthy' : 'moderate'; // Simplified severity
  
  dom.severityBadge.textContent = isHealthy ? t('healthy') : 'Attention Needed';
  dom.severityBadge.className = `severity-badge ${severity}`;

  const conf = Math.round((prediction.confidence || 0) * 100);
  dom.confidenceValue.textContent = conf > 0 ? `${conf}%` : 'N/A';
  dom.confidenceBar.style.width = conf > 0 ? `${conf}%` : '0%';

  dom.descEn.textContent = diagnosis.description_en || '';
  dom.descSn.textContent = diagnosis.description_sn || '';

  renderList(dom.recListEn, diagnosis.recommendations_en || []);
  renderList(dom.recListSn, diagnosis.recommendations_sn || []);

  dom.resultsSection.classList.remove('hidden');
}

function renderList(el, items) {
  el.innerHTML = '';
  items.forEach(it => {
    const li = document.createElement('li');
    li.textContent = it;
    el.appendChild(li);
  });
}

function bindTTS() {
  dom.btnTts.addEventListener('click', () => {
    if(!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    
    let text = `${dom.diseaseName.textContent}. ${state.language === 'sn' ? dom.descSn.textContent : dom.descEn.textContent}`;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = state.language === 'sn' ? 'sn-ZW' : 'en-US';
    window.speechSynthesis.speak(utterance);
  });
}

function showError(msg) {
  dom.errorMessage.textContent = msg;
  dom.errorMessage.classList.remove('hidden');
}
function hideError() {
  dom.errorMessage.classList.add('hidden');
}
function hideResults() {
  dom.resultsSection.classList.add('hidden');
}

// ═══════════════════════════════════════════
// WEATHER API (Open-Meteo) & MARKET MOCKS
// ═══════════════════════════════════════════
async function fetchWeather() {
  // Using coordinates for Harare, Zimbabwe: -17.8252, 31.0335
  const url = "https://api.open-meteo.com/v1/forecast?latitude=-17.8252&longitude=31.0335&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&timezone=Africa%2FHarare";
  try {
    const res = await fetch(url);
    const data = await res.json();
    if(data.current) {
      $('#weather-loading').classList.add('hidden');
      $('#weather-content').classList.remove('hidden');
      
      $('#weather-temp').textContent = `${data.current.temperature_2m}°C`;
      $('#weather-humidity').textContent = `${data.current.relative_humidity_2m}%`;
      $('#weather-wind').textContent = `${data.current.wind_speed_10m} km/h`;
      
      const wc = data.current.weather_code;
      let desc = "Clear";
      if(wc >= 1 && wc <= 3) desc = "Partly Cloudy";
      if(wc >= 51 && wc <= 67) desc = "Rainy";
      if(wc >= 71 && wc <= 77) desc = "Snow";
      $('#weather-desc').textContent = desc;

      const homePill = $('#home-weather-pill');
      if(homePill) {
        homePill.classList.remove('hidden');
        $('#home-weather-temp').textContent = `${data.current.temperature_2m}°C`;
        $('#home-weather-desc').textContent = desc;
      }
    }
  } catch (err) {
    console.error("Failed to fetch weather", err);
    $('#weather-loading').classList.add('hidden');
    $('#weather-content').classList.remove('hidden');
    $('#weather-desc').textContent = "Weather unavailable";
  }
}

function setMarketDate() {
  const d = new Date();
  const dateStr = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  $('#market-date-val').textContent = dateStr;
}
