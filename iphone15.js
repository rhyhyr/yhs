/* ── Navigation ── */
const history = ['s-home'];
let current = 's-home';

function navigate(id) {
    if (id === 'notif-placeholder') { showToast('알림 화면으로 이동합니다'); return; }
    if (id === current) return;
    const prev = document.getElementById(current);
    const next = document.getElementById(id);
    if (!next) { showToast('화면 준비 중입니다'); return; }
    prev.classList.add('exit-left');
    next.classList.add('active');
    setTimeout(() => prev.classList.remove('active', 'exit-left'), 250);
    history.push(id);
    current = id;
}

function back() {
    if (history.length <= 1) return;
    history.pop();
    const prev = current;
    const next = history[history.length - 1];
    const prevEl = document.getElementById(prev);
    const nextEl = document.getElementById(next);
    prevEl.style.transform = 'translateX(24px)';
    prevEl.style.opacity = '0';
    nextEl.classList.add('active');
    nextEl.style.transform = 'translateX(0)';
    nextEl.style.opacity = '1';
    setTimeout(() => {
        prevEl.classList.remove('active');
        prevEl.style.transform = '';
        prevEl.style.opacity = '';
    }, 250);
    current = next;
}

/* ── Toast ── */
let toastTimer;
function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 2200);
}

/* ── Step check toggle ── */
let checked = 2, total = 6;
function toggleStep(row) {
    const cb = row.querySelector('.step-cb');
    const texts = row.querySelectorAll('.step-text,.step-sub');
    const isChecked = cb.classList.contains('checked');
    if (isChecked) {
        cb.classList.remove('checked'); cb.textContent = '';
        cb.classList.add('current');
        texts.forEach(t => t.classList.remove('done'));
        checked = Math.max(0, checked - 1);
    } else {
        cb.classList.remove('current'); cb.classList.add('checked'); cb.textContent = '✓';
        texts.forEach(t => t.classList.add('done'));
        checked = Math.min(total, checked + 1);
    }
    const pct = Math.round(checked / total * 100);
    document.getElementById('prog-fill').style.width = pct + '%';
    document.getElementById('prog-txt').textContent = checked + ' / ' + total + ' 단계 완료';
    document.getElementById('prog-pct').textContent = pct + '%';
    if (checked === total) showToast('🎉 모든 단계를 완료했습니다!');
}

/* ── Info toggle ── */
let infoOpen = true;
function toggleInfo() {
    const p = document.getElementById('info-panel');
    const a = document.getElementById('d87-arrow');
    infoOpen = !infoOpen;
    p.style.display = infoOpen ? 'flex' : 'none';
    a.textContent = infoOpen ? '▾' : '▸';
}

/* ── Toggle switch ── */
function toggleSwitch(el) {
    el.classList.toggle('on');
    el.classList.toggle('off');
    const isOn = el.classList.contains('on');
    showToast(isOn ? '알림이 켜졌습니다' : '알림이 꺼졌습니다');
}

/* ── Filter chip ── */
function filterTag(el, label) {
    el.closest('.filter-row').querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    showToast(label + ' 필터가 적용됐습니다');
}

/* ── Language toggle ── */
function toggleLang(el) { el.classList.toggle('on'); }

/* ── Select chip (onboarding) ── */
function selectChip(el, group) {
    el.closest('.chip-row').querySelectorAll('.sel-chip').forEach(c => c.classList.remove('on'));
    el.classList.add('on');
}

/* ── Calendar render ── */
(function () {
    const evts = {
        '2026-08-10': ['#5B45C2'],
        '2026-08-15': ['#5B45C2', '#D13B3B'],
        '2026-08-20': ['#1A8C5B'],
        '2026-08-25': ['#2155CD'],
    };
    const first = new Date(2026, 7, 1).getDay();
    const days = 31;
    let html = '';
    const cellStyle = 'height:38px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding-top:5px;border-radius:10px;cursor:pointer;transition:background .1s';
    for (let i = 0; i < first; i++) {
        html += `<div style="${cellStyle}"><span style="font-size:13px;color:#C8C5BC">${31 - first + 1 + i}</span></div>`;
    }
    for (let d = 1; d <= days; d++) {
        const key = `2026-08-${String(d).padStart(2, '0')}`;
        const dots = evts[key] || [];
        const isToday = d === 15;
        const bg = isToday ? 'background:#E8EEFB;' : '';
        const tc = isToday ? 'color:#2155CD;font-weight:700;' : 'color:#1A1916;';
        const dotHtml = dots.map(c => `<div style="width:5px;height:5px;border-radius:50%;background:${c}"></div>`).join('');
        html += `<div style="${cellStyle}${bg}"><span style="font-size:13px;${tc}">${d}</span><div style="display:flex;gap:2px;margin-top:2px">${dotHtml}</div></div>`;
    }
    const rem = (first + days) % 7;
    if (rem > 0) for (let i = 1; i <= 7 - rem; i++) html += `<div style="${cellStyle}"><span style="font-size:13px;color:#C8C5BC">${i}</span></div>`;
    document.getElementById('cal-grid').innerHTML = html;
})();

/* ── Visa chat API ── */
const API_BASE_URL = 'http://localhost:8000';

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function addVisaUserMessage(text) {
    const chatArea = document.getElementById('visa-chat-area');
    const msg = document.createElement('div');
    msg.className = 'msg-user';
    msg.innerHTML = `<div class="bubble-user">${escapeHtml(text)}</div>`;
    chatArea.appendChild(msg);
    scrollVisaChatToBottom();
}

function addVisaAIMessage(text) {
    const chatArea = document.getElementById('visa-chat-area');
    const msg = document.createElement('div');
    msg.className = 'msg-ai';
    msg.innerHTML = `
        <div class="ai-av">AI</div>
        <div class="bubble-ai">${escapeHtml(text).replace(/\n/g, '<br>')}</div>
    `;
    chatArea.appendChild(msg);
    scrollVisaChatToBottom();
}

function setVisaSendButtonLoading(isLoading) {
    const btn = document.querySelector('#s-visa .send-btn');
    if (!btn) return;
    btn.disabled = isLoading;
    btn.style.opacity = isLoading ? '0.6' : '1';
    btn.style.pointerEvents = isLoading ? 'none' : 'auto';
    if (isLoading) {
        btn.dataset.originalHtml = btn.innerHTML;
        btn.innerHTML = `<span style="color:#fff;font-size:12px;font-weight:700">...</span>`;
    } else if (btn.dataset.originalHtml) {
        btn.innerHTML = btn.dataset.originalHtml;
    }
}

function scrollVisaChatToBottom() {
    const scrollArea = document.querySelector('#s-visa .scroll-area');
    if (!scrollArea) return;
    scrollArea.scrollTop = scrollArea.scrollHeight;
}

async function sendVisaMessage() {
    const input = document.getElementById('visa-input');
    if (!input) return;
    const text = input.value.trim();
    if (!text) { showToast('질문을 입력해주세요'); return; }

    addVisaUserMessage(text);
    input.value = '';
    setVisaSendButtonLoading(true);

    try {
        const res = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                channel: 'visa',
                user_id: 'user123',
                visa_type: 'D-2'
            })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        addVisaAIMessage(data.answer || '응답은 왔지만 answer 필드가 비어 있어요.');
    } catch (error) {
        console.error('Visa chat API error:', error);
        addVisaAIMessage('서버 연결에 실패했어요. /chat 응답 형식을 확인해주세요.');
    } finally {
        setVisaSendButtonLoading(false);
    }
}

document.getElementById('visa-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') sendVisaMessage();
});

/* ── Main chat API ── */
function addMainUserMessage(text) {
    const chatArea = document.getElementById('main-chat-area');
    if (!chatArea) return;
    const msg = document.createElement('div');
    msg.className = 'msg-user';
    msg.innerHTML = `<div class="bubble-user">${escapeHtml(text)}</div>`;
    chatArea.appendChild(msg);
    scrollMainChatToBottom();
}

function addMainAIMessage(text) {
    const chatArea = document.getElementById('main-chat-area');
    if (!chatArea) return;
    const msg = document.createElement('div');
    msg.className = 'msg-ai';
    msg.innerHTML = `
        <div class="ai-av">AI</div>
        <div class="bubble-ai">${escapeHtml(text).replace(/\n/g, '<br>')}</div>
    `;
    chatArea.appendChild(msg);
    scrollMainChatToBottom();
}

function setMainSendButtonLoading(isLoading) {
    const btn = document.querySelector('#s-main .send-btn');
    if (!btn) return;
    btn.disabled = isLoading;
    btn.style.opacity = isLoading ? '0.6' : '1';
    btn.style.pointerEvents = isLoading ? 'none' : 'auto';
    if (isLoading) {
        if (!btn.dataset.originalHtml) btn.dataset.originalHtml = btn.innerHTML;
        btn.innerHTML = `<span style="color:#fff;font-size:12px;font-weight:700">...</span>`;
    } else if (btn.dataset.originalHtml) {
        btn.innerHTML = btn.dataset.originalHtml;
    }
}

function scrollMainChatToBottom() {
    const scrollArea = document.querySelector('#s-main .scroll-area');
    if (!scrollArea) return;
    scrollArea.scrollTop = scrollArea.scrollHeight;
}

async function sendMainMessage() {
    const input = document.getElementById('main-input');
    if (!input) return;
    const text = input.value.trim();
    if (!text) { showToast('질문을 입력해주세요'); return; }

    addMainUserMessage(text);
    input.value = '';
    setMainSendButtonLoading(true);

    try {
        const res = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                channel: 'main',
                user_id: 'user123'
            })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        addMainAIMessage(data.answer || '응답이 없습니다.');
        if (data.recommended_channel) {
            const label = data.recommended_channel_label || data.recommended_channel;
            showToast(`추천 채널: ${label}`);
        }
    } catch (error) {
        console.error('Main chat API error:', error);
        addMainAIMessage('서버 연결에 실패했어요. /chat 응답 형식을 확인해주세요.');
    } finally {
        setMainSendButtonLoading(false);
    }
}

document.getElementById('main-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') sendMainMessage();
});
