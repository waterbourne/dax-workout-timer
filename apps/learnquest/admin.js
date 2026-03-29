// LearnQuest Admin Panel JavaScript

// ==================== CONFIGURATION ====================
const CONFIG = {
    PIN: '1234',
    STORAGE_KEY: 'learnquest_admin_session',
    LESSONS_KEY: 'learnquest_lessons',
    EVAAN_KEY: 'learnquest_evaan_progress'
};

// ==================== STATE ====================
let currentPIN = '';
let lessons = [];
let evaanProgress = {
    level: 1,
    streak: 0,
    totalXP: 0,
    gems: 0
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    loadLessons();
    loadEvaanProgress();
    checkAuth();
    setupEventListeners();
    setupLivePreviews();
    setDefaultDates();
}

function setDefaultDates() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('solDate').value = today;
    document.getElementById('atlasDate').value = today;
}

// ==================== AUTHENTICATION ====================
function checkAuth() {
    const session = localStorage.getItem(CONFIG.STORAGE_KEY);
    if (session === 'authenticated') {
        showApp();
    } else {
        showLogin();
    }
}

function showLogin() {
    document.getElementById('loginScreen').style.display = 'flex';
    document.getElementById('appContainer').classList.remove('authenticated');
}

function showApp() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('appContainer').classList.add('authenticated');
    updateDashboard();
    loadHistory();
}

function login() {
    if (currentPIN === CONFIG.PIN) {
        localStorage.setItem(CONFIG.STORAGE_KEY, 'authenticated');
        currentPIN = '';
        updatePinDisplay();
        document.getElementById('pinError').classList.remove('show');
        showApp();
        showToast('✅ Welcome to LearnQuest Admin!', 'success');
    } else {
        document.getElementById('pinError').classList.add('show');
        currentPIN = '';
        updatePinDisplay();
        setTimeout(() => {
            document.getElementById('pinError').classList.remove('show');
        }, 2000);
    }
}

function logout() {
    localStorage.removeItem(CONFIG.STORAGE_KEY);
    showLogin();
    showToast('👋 Logged out successfully', 'info');
}

function updatePinDisplay() {
    const dots = document.querySelectorAll('.pin-dot');
    dots.forEach((dot, index) => {
        dot.classList.toggle('filled', index < currentPIN.length);
    });
}

function handlePinInput(num) {
    if (num === 'clear') {
        currentPIN = currentPIN.slice(0, -1);
    } else if (num === 'enter') {
        if (currentPIN.length === 4) {
            login();
        }
    } else {
        if (currentPIN.length < 4) {
            currentPIN += num;
            if (currentPIN.length === 4) {
                setTimeout(() => login(), 200);
            }
        }
    }
    updatePinDisplay();
}

// ==================== NAVIGATION ====================
function navigateTo(page) {
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });

    // Update pages
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });

    // Show target page
    const targetPage = document.getElementById(page === 'dashboard' ? 'dashboardPage' : page + '-page');
    if (targetPage) {
        targetPage.classList.add('active');
    }

    // Refresh data
    if (page === 'dashboard') {
        updateDashboard();
    } else if (page === 'history') {
        loadHistory();
    }
}

// ==================== DASHBOARD ====================
function updateDashboard() {
    const today = new Date().toISOString().split('T')[0];
    const todayLessons = lessons.filter(l => l.date === today).length;
    
    document.getElementById('totalLessons').textContent = lessons.length;
    document.getElementById('todayLessons').textContent = todayLessons;
    document.getElementById('evaanLevel').textContent = evaanProgress.level;
    document.getElementById('evaanStreak').textContent = evaanProgress.streak;
}

// ==================== LESSON MANAGEMENT ====================
function loadLessons() {
    const stored = localStorage.getItem(CONFIG.LESSONS_KEY);
    if (stored) {
        lessons = JSON.parse(stored);
    }
}

function saveLessons() {
    localStorage.setItem(CONFIG.LESSONS_KEY, JSON.stringify(lessons));
}

function loadEvaanProgress() {
    const stored = localStorage.getItem(CONFIG.EVAAN_KEY);
    if (stored) {
        evaanProgress = JSON.parse(stored);
    }
}

function saveEvaanProgress() {
    localStorage.setItem(CONFIG.EVAAN_KEY, JSON.stringify(evaanProgress));
}

function generateId() {
    return 'lesson_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// ==================== FORM HANDLING ====================
function validateForm(type) {
    const form = document.getElementById(type + 'Form');
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });

    return isValid;
}

function saveLesson(type, publish = false) {
    if (!validateForm(type)) {
        showToast('❌ Please fill in all required fields', 'error');
        return;
    }

    let lessonData;
    
    if (type === 'sol') {
        lessonData = {
            id: generateId(),
            type: 'sol',
            date: document.getElementById('solDate').value,
            week: parseInt(document.getElementById('solWeek').value),
            subject: document.getElementById('solSubject').value,
            title: document.getElementById('solTitle').value,
            hook: document.getElementById('solHook').value,
            discovery: document.getElementById('solDiscovery').value,
            connection: document.getElementById('solConnection').value,
            deeper: document.getElementById('solDeeper').value,
            wonderQuestion: document.getElementById('solWonder').value,
            wonderHint: document.getElementById('solWonderHint').value,
            parentPrompt: document.getElementById('solParentPrompt').value,
            xpReward: parseInt(document.getElementById('solXP').value) || 50,
            gemReward: parseInt(document.getElementById('solGems').value) || 5,
            published: publish,
            createdAt: new Date().toISOString()
        };
    } else {
        lessonData = {
            id: generateId(),
            type: 'atlas',
            date: document.getElementById('atlasDate').value,
            week: parseInt(document.getElementById('atlasWeek').value),
            category: document.getElementById('atlasCategory').value,
            title: document.getElementById('atlasTitle').value,
            characterName: document.getElementById('atlasCharName').value,
            characterAge: document.getElementById('atlasCharAge').value,
            characterDetail: document.getElementById('atlasCharDetail').value,
            setting: document.getElementById('atlasSetting').value,
            story: document.getElementById('atlasStory').value,
            wisdom: document.getElementById('atlasWisdom').value,
            yourTurn: document.getElementById('atlasYourTurn').value,
            dinnerDiscussion: document.getElementById('atlasDinner').value,
            xpReward: parseInt(document.getElementById('atlasXP').value) || 50,
            gemReward: parseInt(document.getElementById('atlasGems').value) || 5,
            published: publish,
            createdAt: new Date().toISOString()
        };
    }

    // Check for duplicate dates
    const existingIndex = lessons.findIndex(l => l.date === lessonData.date && l.type === type && !l.id.includes(lessonData.id));
    if (existingIndex >= 0) {
        lessons[existingIndex] = lessonData;
        showToast('📝 Lesson updated!', 'success');
    } else {
        lessons.push(lessonData);
        showToast(publish ? '🚀 Lesson published!' : '💾 Lesson saved!', 'success');
    }

    saveLessons();
    updateDashboard();
    
    if (publish) {
        exportLessonsToJSON();
    }

    return lessonData;
}

function publishLesson(type) {
    const lesson = saveLesson(type, true);
    if (lesson) {
        showModal('🚀 Published!', 'Lesson has been published to the app.', '🎉');
    }
}

function resetForm(type) {
    document.getElementById(type + 'Form').reset();
    setDefaultDates();
    document.querySelectorAll('.form-input.error, .form-select.error, .form-textarea.error').forEach(el => {
        el.classList.remove('error');
    });
    showToast('🔄 Form reset', 'info');
}

// ==================== LIVE PREVIEWS ====================
function setupLivePreviews() {
    // Sol Preview
    const solFields = ['solSubject', 'solTitle', 'solHook', 'solDiscovery', 'solConnection', 'solXP', 'solGems'];
    solFields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', updateSolPreview);
        }
    });

    // Atlas Preview
    const atlasFields = ['atlasCategory', 'atlasTitle', 'atlasStory', 'atlasWisdom', 'atlasXP', 'atlasGems'];
    atlasFields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', updateAtlasPreview);
        }
    });
}

function updateSolPreview() {
    const subject = document.getElementById('solSubject').value || 'MATH';
    document.getElementById('solPreviewSubject').textContent = subject.toUpperCase();
    document.getElementById('solPreviewTitle').textContent = document.getElementById('solTitle').value || 'Your Lesson Title';
    document.getElementById('solPreviewHook').textContent = document.getElementById('solHook').value || 'Your hook will appear here...';
    document.getElementById('solPreviewDiscovery').textContent = document.getElementById('solDiscovery').value || 'Discovery content...';
    document.getElementById('solPreviewConnection').textContent = document.getElementById('solConnection').value || 'Connection content...';
    document.getElementById('solPreviewXP').textContent = (document.getElementById('solXP').value || 50) + ' XP';
    document.getElementById('solPreviewGems').textContent = (document.getElementById('solGems').value || 5) + ' Gems';
}

function updateAtlasPreview() {
    const category = document.getElementById('atlasCategory').value || 'ANCIENT';
    document.getElementById('atlasPreviewCategory').textContent = category.toUpperCase();
    document.getElementById('atlasPreviewTitle').textContent = document.getElementById('atlasTitle').value || 'Your Story Title';
    document.getElementById('atlasPreviewStory').textContent = document.getElementById('atlasStory').value || 'Your story will appear here...';
    document.getElementById('atlasPreviewWisdom').textContent = document.getElementById('atlasWisdom').value || 'The lesson will appear here...';
    document.getElementById('atlasPreviewXP').textContent = (document.getElementById('atlasXP').value || 50) + ' XP';
    document.getElementById('atlasPreviewGems').textContent = (document.getElementById('atlasGems').value || 5) + ' Gems';
}

// ==================== HISTORY ====================
function loadHistory() {
    const historyList = document.getElementById('historyList');
    const typeFilter = document.getElementById('historyTypeFilter').value;
    const subjectFilter = document.getElementById('historySubjectFilter').value;
    const dateFilter = document.getElementById('historyDateFilter').value;

    let filtered = [...lessons];

    if (typeFilter) {
        filtered = filtered.filter(l => l.type === typeFilter);
    }

    if (subjectFilter) {
        filtered = filtered.filter(l => 
            l.subject === subjectFilter || 
            l.category === subjectFilter
        );
    }

    if (dateFilter) {
        filtered = filtered.filter(l => l.date === dateFilter);
    }

    // Sort by date descending
    filtered.sort((a, b) => new Date(b.date) - new Date(a.date));

    if (filtered.length === 0) {
        historyList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <p>No lessons found</p>
            </div>
        `;
        return;
    }

    historyList.innerHTML = filtered.map(lesson => createHistoryItem(lesson)).join('');
}

function createHistoryItem(lesson) {
    const isSol = lesson.type === 'sol';
    const icon = isSol ? '🎯' : '📚';
    const tag = isSol ? 'sol' : 'atlas';
    const tagText = isSol ? lesson.subject : lesson.category;
    const date = new Date(lesson.date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    });

    return `
        <div class="history-item" data-id="${lesson.id}">
            <div class="history-icon">${icon}</div>
            <div class="history-content">
                <div class="history-title">${lesson.title}</div>
                <div class="history-meta">
                    <span>${date}</span>
                    <span class="history-tag ${tag}">${tagText}</span>
                    ${lesson.published ? '<span>✅ Published</span>' : '<span>📝 Draft</span>'}
                </div>
            </div>
            <div class="history-actions">
                <button class="icon-btn" onclick="editLesson('${lesson.id}')" title="Edit">✏️</button>
                <button class="icon-btn delete" onclick="deleteLesson('${lesson.id}')" title="Delete">🗑️</button>
            </div>
        </div>
    `;
}

function filterHistory() {
    loadHistory();
}

function editLesson(id) {
    const lesson = lessons.find(l => l.id === id);
    if (!lesson) return;

    if (lesson.type === 'sol') {
        document.getElementById('solDate').value = lesson.date;
        document.getElementById('solWeek').value = lesson.week;
        document.getElementById('solSubject').value = lesson.subject;
        document.getElementById('solTitle').value = lesson.title;
        document.getElementById('solHook').value = lesson.hook;
        document.getElementById('solDiscovery').value = lesson.discovery;
        document.getElementById('solConnection').value = lesson.connection;
        document.getElementById('solDeeper').value = lesson.deeper;
        document.getElementById('solWonder').value = lesson.wonderQuestion;
        document.getElementById('solWonderHint').value = lesson.wonderHint || '';
        document.getElementById('solParentPrompt').value = lesson.parentPrompt;
        document.getElementById('solXP').value = lesson.xpReward;
        document.getElementById('solGems').value = lesson.gemReward;
        navigateTo('add-sol');
        updateSolPreview();
    } else {
        document.getElementById('atlasDate').value = lesson.date;
        document.getElementById('atlasWeek').value = lesson.week;
        document.getElementById('atlasCategory').value = lesson.category;
        document.getElementById('atlasTitle').value = lesson.title;
        document.getElementById('atlasCharName').value = lesson.characterName;
        document.getElementById('atlasCharAge').value = lesson.characterAge || '';
        document.getElementById('atlasCharDetail').value = lesson.characterDetail || '';
        document.getElementById('atlasSetting').value = lesson.setting;
        document.getElementById('atlasStory').value = lesson.story;
        document.getElementById('atlasWisdom').value = lesson.wisdom;
        document.getElementById('atlasYourTurn').value = lesson.yourTurn;
        document.getElementById('atlasDinner').value = lesson.dinnerDiscussion;
        document.getElementById('atlasXP').value = lesson.xpReward;
        document.getElementById('atlasGems').value = lesson.gemReward;
        navigateTo('add-atlas');
        updateAtlasPreview();
    }

    // Remove old lesson so it gets replaced on save
    lessons = lessons.filter(l => l.id !== id);
    saveLessons();
    
    showToast('📝 Loaded for editing', 'info');
}

function deleteLesson(id) {
    if (!confirm('Are you sure you want to delete this lesson?')) return;
    
    lessons = lessons.filter(l => l.id !== id);
    saveLessons();
    loadHistory();
    updateDashboard();
    showToast('🗑️ Lesson deleted', 'info');
}

// ==================== EXPORT ====================
function exportLessonsToJSON() {
    const lessonsData = {
        lessons: lessons,
        lastUpdated: new Date().toISOString(),
        version: '1.0'
    };

    // Create downloadable file
    const blob = new Blob([JSON.stringify(lessonsData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'lessons.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // Also save to localStorage for the app to access
    localStorage.setItem('learnquest_export', JSON.stringify(lessonsData));
}

// ==================== UI HELPERS ====================
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function showModal(title, text, icon = '🎉') {
    document.getElementById('modalIcon').textContent = icon;
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalText').textContent = text;
    document.getElementById('modalOverlay').classList.add('show');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('show');
}

// ==================== EVENT LISTENERS ====================
function setupEventListeners() {
    // PIN pad
    document.querySelectorAll('.pin-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            handlePinInput(btn.dataset.num);
        });
    });

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', logout);

    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            navigateTo(item.dataset.page);
        });
    });

    // Forms
    document.getElementById('solForm').addEventListener('submit', (e) => {
        e.preventDefault();
        saveLesson('sol');
    });

    document.getElementById('atlasForm').addEventListener('submit', (e) => {
        e.preventDefault();
        saveLesson('atlas');
    });

    // Remove error styling on input
    document.querySelectorAll('.form-input, .form-select, .form-textarea').forEach(field => {
        field.addEventListener('input', function() {
            this.classList.remove('error');
        });
    });

    // Close modal on overlay click
    document.getElementById('modalOverlay').addEventListener('click', (e) => {
        if (e.target === document.getElementById('modalOverlay')) {
            closeModal();
        }
    });
}