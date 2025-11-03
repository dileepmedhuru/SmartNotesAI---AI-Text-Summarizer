// SmartNotes AI - Main JavaScript (Text, PDF, URL Support Only)

// ==================== DOM ELEMENTS ====================
const noteInput = document.getElementById('noteInput');
const wordCount = document.getElementById('wordCount');
const summarizeBtn = document.getElementById('summarizeBtn');
const keyPointsBtn = document.getElementById('keyPointsBtn');
const clearBtn = document.getElementById('clearBtn');
const outputSection = document.getElementById('outputSection');
const summaryResult = document.getElementById('summaryResult');
const keyPointsResult = document.getElementById('keyPointsResult');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');
const outputStats = document.getElementById('outputStats');
const summaryType = document.getElementById('summaryType');
const maxLength = document.getElementById('maxLength');
const minLength = document.getElementById('minLength');

// Upload tab elements
const uploadTabBtns = document.querySelectorAll('.upload-tab-btn');
const uploadTabContents = document.querySelectorAll('.upload-tab-content');

// File upload elements
const fileInput = document.getElementById('fileInput');
const fileDropZone = document.getElementById('fileDropZone');
const browseBtn = document.getElementById('browseBtn');
const fileInfo = document.getElementById('fileInfo');
const removeFileBtn = document.getElementById('removeFileBtn');

// Website URL elements
const websiteUrlInput = document.getElementById('websiteUrlInput');
const processUrlBtn = document.getElementById('processUrlBtn');
const urlInfo = document.getElementById('urlInfo');
const clearUrlBtn = document.getElementById('clearUrlBtn');

// Language elements
const targetLanguage = document.getElementById('targetLanguage');
const detectLanguageBtn = document.getElementById('detectLanguageBtn');
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');

// Download elements
const downloadPdfBtn = document.getElementById('downloadPdfBtn');
const downloadTextBtn = document.getElementById('downloadTextBtn');

// ==================== STATE ====================
let currentSummary = '';
let currentKeyPoints = [];
let currentOriginalText = '';
let currentContentType = 'text';
let currentContentSource = null;
let currentMetadata = {};
let supportedLanguages = {};
let currentDetectedLanguage = 'en';
let isFileUploaded = false;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    initializeEventListeners();
    initializeTheme();
    await loadSupportedLanguages();
    updateWordCount();
    validateForm();
}

// ==================== EVENT LISTENERS ====================
function initializeEventListeners() {
    noteInput.addEventListener('input', function() {
        updateWordCount();
        validateForm();
        if (!isFileUploaded && currentContentType === 'text') {
            debounceLanguageDetection();
        }
    });

    summarizeBtn.addEventListener('click', summarizeText);
    keyPointsBtn.addEventListener('click', extractKeyPoints);
    clearBtn.addEventListener('click', clearAll);
    themeToggle.addEventListener('click', toggleTheme);
    detectLanguageBtn.addEventListener('click', () => detectTextLanguage(true));

    uploadTabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            switchUploadTab(this.dataset.tab);
        });
    });

    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    removeFileBtn.addEventListener('click', removeFile);
    fileDropZone.addEventListener('dragover', handleDragOver);
    fileDropZone.addEventListener('dragleave', handleDragLeave);
    fileDropZone.addEventListener('drop', handleFileDrop);
    fileDropZone.addEventListener('click', () => fileInput.click());

    processUrlBtn.addEventListener('click', processWebsiteUrl);
    clearUrlBtn.addEventListener('click', clearUrlData);
    websiteUrlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') processWebsiteUrl();
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });

    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            copyToClipboard(this.dataset.copy);
        });
    });

    downloadPdfBtn.addEventListener('click', downloadPdf);
    downloadTextBtn.addEventListener('click', downloadText);
}

// ==================== THEME MANAGEMENT ====================
function initializeTheme() {
    const savedTheme = localStorage.getItem('smartnotes-theme') || 'light';
    setTheme(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    localStorage.setItem('smartnotes-theme', theme);
}

// ==================== LANGUAGE MANAGEMENT ====================
async function loadSupportedLanguages() {
    try {
        const response = await fetch('/languages');
        const result = await response.json();
        
        if (result.success) {
            supportedLanguages = result.languages;
            populateLanguageDropdown();
        }
    } catch (error) {
        console.error('Failed to load languages:', error);
    }
}

function populateLanguageDropdown() {
    while (targetLanguage.children.length > 1) {
        targetLanguage.removeChild(targetLanguage.lastChild);
    }
    
    Object.entries(supportedLanguages).forEach(([code, name]) => {
        const option = document.createElement('option');
        option.value = code;
        option.textContent = name;
        targetLanguage.appendChild(option);
    });
}

let languageDetectionTimeout;
function debounceLanguageDetection() {
    clearTimeout(languageDetectionTimeout);
    languageDetectionTimeout = setTimeout(async () => {
        const text = noteInput.value.trim();
        if (text && text.length > 50) {
            await detectTextLanguage(false);
        }
    }, 1000);
}

async function detectTextLanguage(showToast) {
    const text = noteInput.value.trim();
    
    if (!text) {
        if (showToast) showToastMessage('Please enter some text', 'warning');
        return;
    }
    
    if (showToast) showLoading('Detecting language...');
    
    try {
        const response = await fetch('/detect-language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentDetectedLanguage = result.detected_language;
            updateLanguageDisplay(result.detected_language, result.language_name);
            
            if (showToast) {
                showToastMessage(`Detected: ${result.language_name}`, 'info');
            }
        }
    } catch (error) {
        console.error('Language detection error:', error);
    } finally {
        if (showToast) hideLoading();
    }
}

function updateLanguageDisplay(langCode, langName) {
    document.getElementById('detectedLanguage').textContent = `Detected: ${langName}`;
    document.getElementById('languageInfo').style.display = 'block';
}

// ==================== UPLOAD TAB SWITCHING ====================
function switchUploadTab(tabName) {
    uploadTabBtns.forEach(btn => btn.classList.remove('active'));
    uploadTabContents.forEach(content => content.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    if (tabName === 'text-input') {
        currentContentType = 'text';
        currentContentSource = null;
    } else if (tabName === 'file-upload') {
        currentContentType = 'file';
    } else if (tabName === 'url-input') {
        currentContentType = 'url';
    }
}

// ==================== WEBSITE URL PROCESSING ====================
async function processWebsiteUrl() {
    const url = websiteUrlInput.value.trim();
    
    if (!url) {
        showToastMessage('Please enter a website URL', 'warning');
        websiteUrlInput.focus();
        return;
    }
    
    const urlRegex = /^https?:\/\/.+\..+/i;
    
    if (!urlRegex.test(url)) {
        showToastMessage('Invalid URL format. Please enter a complete URL.', 'error');
        displayUrlError('Invalid URL format. Please enter a complete URL (e.g., https://example.com/article)');
        websiteUrlInput.focus();
        return;
    }
    
    processUrlBtn.disabled = true;
    processUrlBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Extracting...';
    
    showLoading('Extracting content from website...');
    
    try {
        const response = await fetch('/process-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        
        const result = await response.json();
        
        if (result.success) {
            noteInput.value = result.text;
            currentOriginalText = result.text;
            currentContentType = 'url';
            currentContentSource = url;
            
            currentMetadata = {
                url_domain: result.domain,
                url_author: result.authors || 'Unknown',
                title: result.title
            };
            
            displayUrlInfo(result);
            updateWordCount();
            validateForm();
            
            if (result.text && result.text.length > 50) {
                setTimeout(() => detectTextLanguage(false), 500);
            }
            
            showToastMessage(`✓ Content extracted: ${result.word_count.toLocaleString()} words`, 'success');
        } else {
            showToastMessage(result.error || 'Failed to extract content', 'error');
            displayUrlError(result.error || 'Unable to extract content from this website.');
        }
    } catch (error) {
        console.error('URL processing error:', error);
        showToastMessage('Network error. Please try again.', 'error');
        displayUrlError('Unable to connect to the server. Please check your connection.');
    } finally {
        hideLoading();
        processUrlBtn.disabled = false;
        processUrlBtn.innerHTML = '<i class="fas fa-download"></i> Extract Content';
    }
}

function displayUrlInfo(data) {
    document.getElementById('urlTitle').textContent = data.title || 'Unknown Title';
    document.getElementById('urlDomain').textContent = data.domain || 'Unknown Domain';
    document.getElementById('urlAuthor').textContent = data.authors || 'Unknown Author';
    document.getElementById('urlWords').textContent = (data.word_count || 0).toLocaleString();
    document.getElementById('urlReadingTime').textContent = `${data.reading_time || estimateReadingTime(data.word_count)} min`;
    
    urlInfo.style.display = 'block';
    const errorBox = document.querySelector('.url-error-box');
    if (errorBox) errorBox.remove();
    
    urlInfo.classList.add('success');
    setTimeout(() => {
        urlInfo.classList.remove('success');
    }, 2000);
}

function displayUrlError(errorMessage) {
    const existingError = document.querySelector('.url-error-box');
    if (existingError) existingError.remove();
    
    const errorBox = document.createElement('div');
    errorBox.className = 'url-error url-error-box';
    errorBox.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <span>${errorMessage}</span>
    `;
    
    const inputBox = document.querySelector('#url-input .url-input-box');
    if (inputBox) {
        inputBox.after(errorBox);
    }
    
    urlInfo.style.display = 'none';
}

function clearUrlData() {
    websiteUrlInput.value = '';
    urlInfo.style.display = 'none';
    
    const errorBox = document.querySelector('.url-error-box');
    if (errorBox) errorBox.remove();
    
    if (currentContentType === 'url') {
        noteInput.value = '';
        currentOriginalText = '';
        currentContentType = 'text';
        currentContentSource = null;
        currentMetadata = {};
        updateWordCount();
        validateForm();
    }
}

function estimateReadingTime(wordCount) {
    const wordsPerMinute = 200;
    return Math.max(1, Math.round(wordCount / wordsPerMinute));
}

// ==================== FILE UPLOAD ====================
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) uploadFile(file);
}

function handleDragOver(event) {
    event.preventDefault();
    fileDropZone.classList.add('drag-over');
}

function handleDragLeave(event) {
    event.preventDefault();
    fileDropZone.classList.remove('drag-over');
}

function handleFileDrop(event) {
    event.preventDefault();
    fileDropZone.classList.remove('drag-over');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) uploadFile(files[0]);
}

async function uploadFile(file) {
    if (!validateFile(file)) return;
    
    showLoading('Processing file...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            noteInput.value = result.text;
            currentOriginalText = result.text;
            currentContentType = 'file';
            currentContentSource = result.filename;
            
            currentMetadata = {
                filename: result.filename,
                word_count: result.word_count,
                file_type: result.file_type,
                detected_language: result.detected_language,
                language_name: result.language_name
            };
            
            displayFileInfo(result);
            updateLanguageDisplay(result.detected_language, result.language_name);
            
            isFileUploaded = true;
            updateWordCount();
            validateForm();
            
            showToastMessage(`✓ File processed: ${result.word_count.toLocaleString()} words extracted`, 'success');
        } else {
            showToastMessage(result.error || 'File upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToastMessage('File upload failed', 'error');
    } finally {
        hideLoading();
    }
}

function validateFile(file) {
    const allowedTypes = ['application/pdf', 'text/plain', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-powerpoint'];
    const maxSize = 16 * 1024 * 1024;
    
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|txt|docx|doc|pptx|ppt)$/i)) {
        showToastMessage('Please upload PDF, TXT, DOCX, or PPTX files', 'error');
        return false;
    }
    
    if (file.size > maxSize) {
        showToastMessage('File size must be less than 16MB', 'error');
        return false;
    }
    
    return true;
}

function displayFileInfo(fileData) {
    document.getElementById('fileName').textContent = fileData.filename;
    document.getElementById('fileSize').textContent = formatFileSize(fileData.file_size || 0);
    document.getElementById('fileType').textContent = fileData.file_type.toUpperCase();
    document.getElementById('extractedWords').textContent = fileData.word_count;
    
    if (fileData.detected_language && fileData.language_name) {
        document.getElementById('fileLanguageName').textContent = fileData.language_name;
        document.getElementById('fileLanguage').style.display = 'flex';
    }
    
    fileInfo.style.display = 'block';
}

function removeFile() {
    fileInfo.style.display = 'none';
    fileDropZone.style.display = 'block';
    fileInput.value = '';
    
    if (currentContentType === 'file') {
        noteInput.value = '';
        currentOriginalText = '';
        currentContentType = 'text';
        currentContentSource = null;
        currentMetadata = {};
        isFileUploaded = false;
        updateWordCount();
        validateForm();
    }
    
    showToastMessage('File removed', 'info');
}

// ==================== SUMMARIZATION ====================
async function summarizeText() {
    const text = noteInput.value.trim();
    
    if (!text) {
        showToastMessage('Please enter text to summarize', 'warning');
        return;
    }
    
    if (text.split(' ').length < 10) {
        showToastMessage('Text is too short to summarize', 'warning');
        return;
    }
    
    showLoading('Generating AI summary...');
    
    try {
        const requestData = {
            text: text,
            max_length: parseInt(maxLength.value),
            min_length: parseInt(minLength.value),
            summary_type: summaryType.value,
            content_type: currentContentType,
            content_source: currentContentSource,
            ...currentMetadata
        };
        
        if (targetLanguage.value) {
            requestData.target_language = targetLanguage.value;
        }
        
        const response = await fetch('/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentSummary = result.summary;
            currentOriginalText = text;
            
            displaySummary(result);
            showOutputSection();
            switchTab('summary');
            
            showToastMessage('✓ Summary generated successfully!', 'success');
        } else {
            showToastMessage(result.error || 'Failed to generate summary', 'error');
        }
    } catch (error) {
        console.error('Summarization error:', error);
        showToastMessage('Failed to generate summary', 'error');
    } finally {
        hideLoading();
    }
}

async function extractKeyPoints() {
    const text = noteInput.value.trim();
    
    if (!text) {
        showToastMessage('Please enter text to extract key points', 'warning');
        return;
    }
    
    showLoading('Extracting key points...');
    
    try {
        const requestData = {
            text: text,
            num_points: 5
        };
        
        if (targetLanguage.value) {
            requestData.target_language = targetLanguage.value;
        }
        
        const response = await fetch('/key-points', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentKeyPoints = result.key_points;
            currentOriginalText = text;
            
            displayKeyPoints(result.key_points);
            showOutputSection();
            switchTab('keypoints');
            
            showToastMessage('✓ Key points extracted!', 'success');
        } else {
            showToastMessage(result.error || 'Failed to extract key points', 'error');
        }
    } catch (error) {
        console.error('Key points error:', error);
        showToastMessage('Failed to extract key points', 'error');
    } finally {
        hideLoading();
    }
}

// ==================== DISPLAY FUNCTIONS ====================
function displaySummary(result) {
    summaryResult.innerHTML = `<p>${result.summary}</p>`;
    
    const compressionRatio = result.compression_ratio || 0;
    let statsText = `${result.summary_length} words • ${compressionRatio}% compression`;
    
    if (currentContentType !== 'text') {
        const typeIcons = {
            'file': 'fa-file',
            'url': 'fa-globe'
        };
        const icon = typeIcons[currentContentType] || 'fa-file';
        statsText += ` • <i class="${icon}"></i> ${currentContentType.toUpperCase()}`;
    }
    
    if (result.detected_language && result.language_name) {
        statsText += ` • Source: ${result.language_name}`;
    }
    
    outputStats.innerHTML = statsText;
}

function displayKeyPoints(keyPoints) {
    if (keyPoints && keyPoints.length > 0) {
        const listHTML = keyPoints.map(point => `<li>${point}</li>`).join('');
        keyPointsResult.innerHTML = `<ul>${listHTML}</ul>`;
    } else {
        keyPointsResult.innerHTML = '<p>No key points extracted.</p>';
    }
}

function showOutputSection() {
    outputSection.style.display = 'block';
    outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');
}

// ==================== UTILITY FUNCTIONS ====================
function updateWordCount() {
    const text = noteInput.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    wordCount.textContent = words;
}

function validateForm() {
    const hasText = noteInput.value.trim().length > 0;
    summarizeBtn.disabled = !hasText;
    keyPointsBtn.disabled = !hasText;
    detectLanguageBtn.disabled = !hasText;
}

function clearAll() {
    noteInput.value = '';
    outputSection.style.display = 'none';
    summaryResult.innerHTML = '';
    keyPointsResult.innerHTML = '';
    
    currentSummary = '';
    currentKeyPoints = [];
    currentOriginalText = '';
    currentContentType = 'text';
    currentContentSource = null;
    currentMetadata = {};
    
    clearUrlData();
    removeFile();
    
    document.getElementById('languageInfo').style.display = 'none';
    
    updateWordCount();
    validateForm();
    showToastMessage('All content cleared', 'info');
}

async function copyToClipboard(type) {
    let textToCopy = '';
    
    if (type === 'summary') {
        textToCopy = currentSummary;
    } else if (type === 'keypoints') {
        textToCopy = currentKeyPoints.join('\n• ');
        if (textToCopy) textToCopy = '• ' + textToCopy;
    }
    
    if (!textToCopy) {
        showToastMessage('Nothing to copy', 'warning');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(textToCopy);
        showToastMessage('Copied to clipboard!', 'success');
    } catch (error) {
        const textArea = document.createElement('textarea');
        textArea.value = textToCopy;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showToastMessage('Copied to clipboard!', 'success');
    }
}

async function downloadPdf() {
    if (!currentSummary && currentKeyPoints.length === 0) {
        showToastMessage('No content to download', 'warning');
        return;
    }
    
    showLoading('Generating PDF...');
    
    try {
        const metadata = { ...currentMetadata };
        
        const response = await fetch('/download-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                original_text: currentOriginalText,
                summary: currentSummary,
                key_points: currentKeyPoints,
                metadata: metadata
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `smartnotes_summary_${new Date().getTime()}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToastMessage('PDF downloaded!', 'success');
        } else {
            showToastMessage('Failed to generate PDF', 'error');
        }
    } catch (error) {
        console.error('PDF download error:', error);
        showToastMessage('Failed to download PDF', 'error');
    } finally {
        hideLoading();
    }
}

async function downloadText() {
    if (!currentSummary && currentKeyPoints.length === 0) {
        showToastMessage('No content to download', 'warning');
        return;
    }
    
    showLoading('Generating text file...');
    
    try {
        const metadata = { ...currentMetadata };
        
        const response = await fetch('/download-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                summary: currentSummary,
                key_points: currentKeyPoints,
                metadata: metadata,
                original_filename: currentMetadata.filename || currentContentType
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `smartnotes_summary_${new Date().getTime()}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToastMessage('Text file downloaded!', 'success');
        } else {
            showToastMessage('Failed to generate text file', 'error');
        }
    } catch (error) {
        console.error('Text download error:', error);
        showToastMessage('Failed to download text file', 'error');
    } finally {
        hideLoading();
    }
}

function showLoading(message = 'Processing...') {
    loadingText.textContent = message;
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

function showToastMessage(message, type = 'success') {
    toastMessage.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloatpython((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}