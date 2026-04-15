/**
 * AIEMCS - Chat Interface JavaScript
 * With conversation history / memory support.
 */

const API     = 'http://localhost:8000';
const msgEl   = document.getElementById('messages');
const inputEl = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

// Store full conversation history
let conversationHistory = [];
let sessionId = crypto.randomUUID();

// ── Helpers ──────────────────────────────────────────────────────────────────

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function scrollBottom() {
  msgEl.scrollTop = msgEl.scrollHeight;
}

function appendMessage(role, text, results = []) {
  const wrap   = document.createElement('div');
  wrap.className = `message ${role}`;

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.textContent = text;

  const time = document.createElement('span');
  time.className = 'message-time';
  time.textContent = now();

  wrap.appendChild(bubble);
  wrap.appendChild(time);

  if (role === 'bot' && results.length) {
    const grid = document.createElement('div');
    grid.className = 'results-grid';
    results.forEach(r => grid.appendChild(buildResultCard(r)));
    wrap.appendChild(grid);
  }

  msgEl.appendChild(wrap);
  scrollBottom();
}

function buildResultCard(r) {
  const matchLabel = {
    exact:         'Exact Match',
    same_category: 'Same Category',
    alternative:   'Alternative',
    nearest_time:  'Nearest Time',
  }[r.match_type] || r.match_type;

  const card = document.createElement('div');
  card.className = 'result-card';
  card.innerHTML = `
    <h4>${r.equipment_name}</h4>
    <div class="meta">📋 ${r.equipment_model_details || 'N/A'}</div>
    <div class="meta">📍 ${r.block_location || '—'}</div>
    <div class="meta">🔢 Qty: ${r.quantity || 1}</div>
    <div style="margin-top:0.5rem;display:flex;gap:0.4rem;flex-wrap:wrap;">
      <span class="badge badge-${r.working_status}">${r.working_status || 'good'}</span>
      <span class="badge badge-${r.match_type}">${matchLabel}</span>
    </div>
    ${r.suggested_day ? `<div class="meta mt-1" style="color:var(--warning);">⏰ Try: ${r.suggested_day} ${r.suggested_slot || ''}</div>` : ''}
  `;
  return card;
}

function showTyping() {
  const wrap = document.createElement('div');
  wrap.className = 'message bot';
  wrap.id = 'typing';
  wrap.innerHTML = `<div class="message-bubble" style="padding:0.6rem 1rem;"><span class="spinner"></span></div>`;
  msgEl.appendChild(wrap);
  scrollBottom();
}

function removeTyping() {
  const t = document.getElementById('typing');
  if (t) t.remove();
}

// ── Core send ─────────────────────────────────────────────────────────────────

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = '';
  sendBtn.disabled = true;

  // Add user message to UI
  appendMessage('user', text);

  // Add to conversation history
  conversationHistory.push({ role: 'user', content: text });

  showTyping();

  try {
    const res = await fetch(`${API}/chat`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        message:    text,
        session_id: sessionId,
        history:    conversationHistory.slice(-10), // send last 10 messages
      }),
    });

    removeTyping();

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
      const errMsg = `⚠️ Error: ${err.detail || 'Something went wrong.'}`;
      appendMessage('bot', errMsg);
      conversationHistory.push({ role: 'assistant', content: errMsg });
      return;
    }

    const data = await res.json();
    const answer = data.answer || 'No response.';

    appendMessage('bot', answer, data.results || []);

    // Add assistant response to history
    conversationHistory.push({ role: 'assistant', content: answer });

  } catch (e) {
    removeTyping();
    const errMsg = '⚠️ Cannot reach the AIEMCS server.\n\nMake sure the backend is running:\n  python -m uvicorn backend.main:app --reload';
    appendMessage('bot', errMsg);
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

function sendSuggestion(el) {
  inputEl.value = el.textContent.trim();
  sendMessage();
}

// ── Clear chat button ─────────────────────────────────────────────────────────

function clearChat() {
  conversationHistory = [];
  sessionId = crypto.randomUUID();
  msgEl.innerHTML = '';
  appendMessage('bot',
    '👋 Hello! I\'m the AIEMCS Equipment Assistant.\n\n' +
    'Ask me about equipment availability across any block. You can specify:\n' +
    '• Equipment type (laptop, MRI, CNC…)\n' +
    '• Block & room (Block E, A_101…)\n' +
    '• Day & time slot\n' +
    '• Specifications (i7, 16GB RAM…)'
  );
}