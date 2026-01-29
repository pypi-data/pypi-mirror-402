const ui = {
    url: document.getElementById('urlInput'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    infoGrid: document.getElementById('infoGrid'),
    title: document.getElementById('videoTitle'),
    meta: document.getElementById('videoMeta'),
    thumb: document.getElementById('thumbImg'),
    quality: document.getElementById('qualitySelect'),
    status: document.getElementById('statusMsg'),
    progress: document.getElementById('progressArea'),
    fill: document.getElementById('barFill'),
    percent: document.getElementById('progPercent'),
    percent: document.getElementById('progPercent'),
    speed: document.getElementById('progSpeed'),
    actionButtons: document.getElementById('actionButtons'),
    pathInput: document.getElementById('savePath'),
    pathBtn: document.getElementById('changePathBtn'),
    pathIcon: document.querySelector('.path-icon') // New
};

let lastDownloadedFilename = null;

function getQualityLabel(height) {
    const h = parseInt(height);
    if (!h) return '자동';
    if (h >= 4320) return '8K 초현실';
    if (h >= 2160) return '4K 영화급';
    if (h >= 1440) return 'QHD 매우 선명';
    if (h >= 1080) return 'FHD 표준';
    if (h >= 720) return 'HD 깔끔';
    if (h >= 480) return 'SD 데이터 절약';
    return `${h}p 저화질`;
}

function analyzeUrl() {
    const url = ui.url.value.trim();
    if (!url) return showStatus('링크를 입력해주세요', 'error');

    setLoading(ui.analyzeBtn, true);
    ui.infoGrid.classList.remove('active');
    ui.progress.classList.remove('active');
    ui.actionButtons.style.display = 'none';
    showStatus('');

    fetch('/api/info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);

            ui.title.textContent = data.title;
            ui.meta.textContent = `${data.duration} • ${data.uploader}`;
            ui.thumb.src = data.thumbnail;

            // Custom Quality Logic
            ui.quality.innerHTML = '';

            // formats is sorted by height desc from backend
            // Filter unique heights for cleaner dropdown, prefer highest filesize if multiple same height? No, just list distinct heights
            const seenHeights = new Set();
            data.formats.forEach(fmt => {
                if (!fmt.height) return;
                // Round slightly or just use raw? yt-dlp returns exact.
                // Some formats might be 1080, others 1081? usually standard.

                if (!seenHeights.has(fmt.height)) {
                    seenHeights.add(fmt.height);
                    const opt = document.createElement('option');
                    opt.value = fmt.format_id;

                    let sizeStr = '';
                    if (fmt.filesize) {
                        sizeStr = ` (${(fmt.filesize / 1024 / 1024).toFixed(1)}MB)`;
                    }

                    opt.textContent = `${getQualityLabel(fmt.height)} - ${fmt.height}p${sizeStr}`;
                    ui.quality.appendChild(opt);
                }
            });

            // Add "Audio Only" placeholder if no video? No, audio button is separate.

            ui.infoGrid.classList.add('active');
        })
        .catch(err => {
            showStatus(err.message || '분석 중 오류 발생', 'error');
        })
        .finally(() => {
            setLoading(ui.analyzeBtn, false);
        });
}

async function download(type) {
    const url = ui.url.value.trim();
    const formatId = ui.quality.value;

    // Find button
    const btn = event.currentTarget; // Simple trick or pass logic
    setLoading(btn, true);

    ui.progress.classList.add('active');
    updateProgress(0, '연결 중...');

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                type: type,
                format_id: type === 'video' ? formatId : null
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);
                    if (data.status === 'downloading') {
                        updateProgress(data.percent, data.speed);
                    } else if (data.status === 'processing') {
                        updateProgress(100, '저장 중... 잠시만요');
                    } else if (data.status === 'complete') {
                        updateProgress(100, '완료!');
                        showStatus(`다운로드 완료: ${data.filename}`, 'success');
                        lastDownloadedFilename = data.filename;
                        ui.actionButtons.style.display = 'flex';
                        setTimeout(() => {
                            // Optional: Reset UI or keep it
                            setLoading(btn, false);
                        }, 1000);
                        return;
                    } else if (data.status === 'error') {
                        throw new Error(data.message);
                    }
                } catch (e) { }
            }
        }
    } catch (err) {
        showStatus('실패: ' + err.message, 'error');
        setLoading(btn, false);
    }
}

function updateProgress(percent, speed) {
    ui.fill.style.width = percent + '%';
    ui.percent.textContent = percent + '%';
    ui.speed.textContent = speed;
}

function showStatus(msg, type) {
    ui.status.textContent = msg;
    ui.status.className = 'status-msg ' + (type || '');
}

function setLoading(btn, isLoading) {
    if (isLoading) {
        btn.classList.add('loading');
        btn.disabled = true;
    } else {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// Theme Handling
const toggleBtn = document.getElementById('themeToggle');
const icon = toggleBtn.querySelector('i');

function setTheme(isDark) {
    if (isDark) {
        document.body.classList.remove('light-theme');
        document.body.classList.add('dark-theme');
        icon.className = 'fas fa-sun';
    } else {
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        icon.className = 'fas fa-moon';
    }
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Initialize Theme
const savedTheme = localStorage.getItem('theme');
const sysDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

if (savedTheme === 'dark') {
    setTheme(true);
} else if (savedTheme === 'light') {
    setTheme(false);
} else {
    // If no save, follow system
    setTheme(sysDark);
}

toggleBtn.addEventListener('click', () => {
    // Current state check
    const isCurrentDark = document.body.classList.contains('dark-theme');
    setTheme(!isCurrentDark);
});

function openFolder() {
    fetch('/api/open_folder', { method: 'POST' });
}

function openFile() {
    if (!lastDownloadedFilename) return;
    fetch('/api/open_file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: lastDownloadedFilename })
    });
}

function loadPath() {
    fetch('/api/settings/path')
        .then(res => res.json())
        .then(data => {
            if (data.path) {
                ui.pathInput.value = data.path;
            }
        });
}

function savePath() {
    const newPath = ui.pathInput.value.trim();
    if (!newPath) return;

    fetch('/api/settings/path', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: newPath })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                ui.pathInput.value = data.path;
                ui.pathInput.readOnly = true;
                ui.pathInput.classList.remove('editing');
                ui.pathBtn.innerHTML = '<i class="fas fa-pen"></i>';
                showStatus('저장 경로가 변경되었습니다.', 'success');
            } else {
                showStatus(data.error, 'error');
            }
        })
        .catch(err => showStatus('경로 저장 실패', 'error'));
}

if (ui.pathBtn) {
    ui.pathBtn.addEventListener('click', () => {
        if (ui.pathInput.readOnly) {
            ui.pathInput.readOnly = false;
            ui.pathInput.focus();
            ui.pathInput.classList.add('editing');
            ui.pathBtn.innerHTML = '<i class="fas fa-check"></i>';
        } else {
            savePath();
        }
    });

    ui.pathInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            savePath();
        }
    });
}

if (ui.pathIcon) {
    ui.pathIcon.style.cursor = 'pointer';
    ui.pathIcon.title = "폴더 찾기 (탐색기 열기)";
    ui.pathIcon.addEventListener('click', () => {
        // Visual feedback
        ui.pathIcon.style.opacity = '0.5';

        fetch('/api/select_folder', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                ui.pathIcon.style.opacity = '1';
                if (data.success) {
                    ui.pathInput.value = data.path;
                    showStatus('저장 경로가 변경되었습니다.', 'success');
                } else if (data.error) {
                    showStatus('오류: ' + data.error, 'error');
                }
            })
            .catch(err => {
                ui.pathIcon.style.opacity = '1';
                showStatus('폴더 선택 창 호출 실패', 'error');
            });
    });
}

loadPath();
