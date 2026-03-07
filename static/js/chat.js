/* ═══════════════════════════════════════════
   NexChat — chat.js
   All socket.io + UI logic
═══════════════════════════════════════════ */

const socket = io();

// State
let currentRoom   = null;
let currentType   = null;   // 'room' | 'dm'
let currentRid    = null;   // numeric id
let typingTimer   = null;
let isTyping      = false;
let typingTimeout = null;

// DOM
const welcomeScreen = document.getElementById('welcomeScreen');
const chatView      = document.getElementById('chatView');
const messagesArea  = document.getElementById('messagesArea');
const msgInput      = document.getElementById('msgInput');
const sendBtn       = document.getElementById('sendBtn');
const typingBar     = document.getElementById('typingBar');
const typingText    = document.getElementById('typingText');
const chatHeaderName= document.getElementById('chatHeaderName');
const chatHeaderSub = document.getElementById('chatHeaderSub');
const chatHeaderAva = document.getElementById('chatHeaderAva');
const sidebar       = document.getElementById('sidebar');
const chatPanel     = document.getElementById('chatPanel');

/* ─── Open a chat ─────────────────────────── */
function openRoom(roomKey, label, type, rid) {
  // Leave previous room
  if (currentRoom) socket.emit('leave', { room: currentRoom });

  // Mark active row
  document.querySelectorAll('.chat-row').forEach(r => r.classList.remove('active'));
  const rowId = type === 'group' ? `row-room-${rid}` : `row-dm-${rid}`;
  const row = document.getElementById(rowId);
  if (row) row.classList.add('active');

  // Update state
  currentRoom = roomKey;
  currentType = type;
  currentRid  = rid;

  // Update header
  chatHeaderName.textContent = (type === 'group' ? '# ' : '') + label;
  chatHeaderSub.textContent  = type === 'group' ? 'Group chat' : 'Direct message';
  chatHeaderAva.textContent  = label[0].toUpperCase();
  chatHeaderAva.style.background = type === 'group'
    ? 'linear-gradient(135deg,#2d5f8a,#1a4a6e)'
    : 'linear-gradient(135deg,#5c3a8a,#3a2060)';
  chatHeaderAva.style.color = type === 'group' ? '#aad4f5' : '#d4aaf5';

  // Show chat view
  welcomeScreen.style.display = 'none';
  chatView.style.display = 'flex';

  // Mobile: slide in
  chatPanel.classList.add('visible');
  sidebar.classList.add('hidden');

  // Load history then join socket room
  loadHistory(type === 'group' ? 'room' : 'dm', rid, roomKey);
}

function closeChat() {
  chatPanel.classList.remove('visible');
  sidebar.classList.remove('hidden');
}

/* ─── Load message history ────────────────── */
function loadHistory(histType, rid, roomKey) {
  messagesArea.innerHTML = '<div class="msgs-loader">Loading…</div>';

  fetch(`/history/${histType}/${rid}`)
    .then(r => r.json())
    .then(msgs => {
      messagesArea.innerHTML = '';
      if (msgs.length === 0) {
        messagesArea.innerHTML = '<div class="msgs-loader">No messages yet. Say hello! 👋</div>';
      } else {
        msgs.forEach(m => appendMessage(m.username, m.message, m.timestamp, m.own));
      }
      scrollBottom();
      // Now join socket room
      socket.emit('join', { room: roomKey });
      msgInput.focus();
    })
    .catch(() => {
      messagesArea.innerHTML = '<div class="msgs-loader">Could not load messages.</div>';
      socket.emit('join', { room: roomKey });
    });
}

/* ─── Send message ────────────────────────── */
function sendMessage() {
  const content = msgInput.value.trim();
  if (!content || !currentRoom) return;

  socket.emit('message', { room: currentRoom, content });
  msgInput.value = '';
  msgInput.focus();

  // Stop typing
  if (isTyping) {
    socket.emit('stop_typing', { room: currentRoom });
    isTyping = false;
  }
}

/* ─── Input events ────────────────────────── */
msgInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

msgInput.addEventListener('input', () => {
  if (!currentRoom) return;

  if (!isTyping) {
    isTyping = true;
    socket.emit('typing', { room: currentRoom });
  }
  clearTimeout(typingTimeout);
  typingTimeout = setTimeout(() => {
    isTyping = false;
    socket.emit('stop_typing', { room: currentRoom });
  }, 2000);
});

/* ─── Socket events ────────────────────────── */
socket.on('message', data => {
  if (data.room !== currentRoom) return;
  const isMe = data.uid === ME.id;
  appendMessage(data.username, data.message, data.timestamp, isMe);
  scrollBottom();
});

socket.on('typing', data => {
  typingText.textContent = `${data.username} is typing`;
  typingBar.style.display = 'flex';
  clearTimeout(typingTimer);
  typingTimer = setTimeout(() => {
    typingBar.style.display = 'none';
  }, 3000);
});

socket.on('stop_typing', () => {
  typingBar.style.display = 'none';
});

/* ─── Append a message bubble ─────────────── */
function appendMessage(username, content, timestamp, isMe) {
  // Remove loader if present
  const loader = messagesArea.querySelector('.msgs-loader');
  if (loader) loader.remove();

  const row = document.createElement('div');
  row.className = `msg-row ${isMe ? 'me' : 'them'}`;

  const senderHtml = (!isMe)
    ? `<div class="msg-sender">${esc(username)}</div>`
    : '';

  row.innerHTML = `
    ${senderHtml}
    <div class="msg-bubble">
      ${esc(content)}
      <span class="msg-time">${timestamp}</span>
    </div>
  `;

  messagesArea.appendChild(row);
}

/* ─── Helpers ─────────────────────────────── */
function scrollBottom() {
  requestAnimationFrame(() => {
    messagesArea.scrollTop = messagesArea.scrollHeight;
  });
}

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
