from datetime import datetime
import sqlite3
from flask import Flask, request, jsonify, session, render_template_string
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret"
socketio = SocketIO(app, cors_allowed_origins="*")
DB_PATH = "systemio.db"

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SystemIO MVP</title>
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #f4f6f8;
      color: #1f2937;
    }
    .app {
      display: grid;
      grid-template-columns: 320px 1fr;
      height: 100vh;
    }
    .sidebar {
      border-right: 1px solid #d1d5db;
      background: #fff;
      padding: 16px;
      overflow: auto;
    }
    .main {
      display: flex;
      flex-direction: column;
      height: 100vh;
    }
    .panel {
      background: #fff;
      border: 1px solid #d1d5db;
      border-radius: 10px;
      padding: 12px;
      margin-bottom: 12px;
    }
    .hidden { display: none; }
    input, button, textarea {
      width: 100%;
      padding: 10px 12px;
      margin-top: 8px;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
      font-size: 14px;
    }
    button {
      cursor: pointer;
      border: none;
      background: #2563eb;
      color: white;
      font-weight: 600;
    }
    button.secondary { background: #475569; }
    button.danger { background: #dc2626; }
    .dialogs {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .dialog-item {
      padding: 10px 12px;
      background: #f8fafc;
      border: 1px solid #dbe3ea;
      border-radius: 8px;
      cursor: pointer;
    }
    .dialog-item.active {
      background: #dbeafe;
      border-color: #93c5fd;
    }
    .chat-header {
      background: #fff;
      border-bottom: 1px solid #d1d5db;
      padding: 16px;
      font-weight: 700;
    }
    .messages {
      flex: 1;
      overflow: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .message {
      max-width: 70%;
      padding: 10px 12px;
      border-radius: 10px;
      background: #fff;
      border: 1px solid #d1d5db;
    }
    .message.me {
      align-self: flex-end;
      background: #dbeafe;
      border-color: #93c5fd;
    }
    .meta {
      font-size: 12px;
      opacity: 0.7;
      margin-bottom: 4px;
    }
    .composer {
      display: grid;
      grid-template-columns: 1fr 140px;
      gap: 12px;
      padding: 16px;
      border-top: 1px solid #d1d5db;
      background: #fff;
    }
    .row { display: flex; gap: 8px; }
    .row > * { flex: 1; }
    .status {
      font-size: 13px;
      margin-top: 8px;
      color: #334155;
      min-height: 18px;
    }
    .muted { color: #64748b; font-size: 13px; }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="panel">
        <h3 style="margin:0 0 8px 0;">SystemIO</h3>
        <div id="authBlock">
          <div class="row">
            <button id="showLoginBtn" class="secondary">Вход</button>
            <button id="showRegisterBtn">Регистрация</button>
          </div>

          <div id="loginForm" class="panel" style="margin-top:12px;">
            <strong>Вход</strong>
            <input id="loginLogin" placeholder="Логин" />
            <input id="loginPassword" type="password" placeholder="Пароль" />
            <button id="loginBtn">Войти</button>
          </div>

          <div id="registerForm" class="panel hidden" style="margin-top:12px;">
            <strong>Регистрация</strong>
            <input id="registerDisplayName" placeholder="Имя" />
            <input id="registerLogin" placeholder="Логин" />
            <input id="registerPassword" type="password" placeholder="Пароль" />
            <button id="registerBtn">Создать аккаунт</button>
          </div>
        </div>

        <div id="userBlock" class="hidden">
          <div><strong id="currentUserName"></strong></div>
          <div class="muted" id="currentUserLogin"></div>
          <button id="logoutBtn" class="danger">Выйти</button>
        </div>

        <div class="status" id="statusBox"></div>
      </div>

      <div class="panel hidden" id="createDialogPanel">
        <strong>Новый диалог</strong>
        <input id="peerLogin" placeholder="Логин собеседника" />
        <button id="createDialogBtn">Создать / открыть</button>
      </div>

      <div class="panel hidden" id="dialogsPanel">
        <strong>Диалоги</strong>
        <div class="dialogs" id="dialogsList" style="margin-top:10px;"></div>
      </div>
    </aside>

    <main class="main">
      <div class="chat-header" id="chatTitle">Выберите диалог</div>
      <div class="messages" id="messages"></div>
      <div class="composer hidden" id="composer">
        <textarea id="messageInput" rows="2" placeholder="Введите сообщение"></textarea>
        <button id="sendBtn">Отправить</button>
      </div>
    </main>
  </div>

  <script>
    const state = {
      me: null,
      dialogs: [],
      activeDialogId: null,
      socket: null,
      joinedRooms: new Set(),
    };

    const els = {
      authBlock: document.getElementById('authBlock'),
      userBlock: document.getElementById('userBlock'),
      currentUserName: document.getElementById('currentUserName'),
      currentUserLogin: document.getElementById('currentUserLogin'),
      statusBox: document.getElementById('statusBox'),
      loginForm: document.getElementById('loginForm'),
      registerForm: document.getElementById('registerForm'),
      dialogsPanel: document.getElementById('dialogsPanel'),
      createDialogPanel: document.getElementById('createDialogPanel'),
      dialogsList: document.getElementById('dialogsList'),
      chatTitle: document.getElementById('chatTitle'),
      messages: document.getElementById('messages'),
      composer: document.getElementById('composer'),
      messageInput: document.getElementById('messageInput'),
    };

    function setStatus(text) {
      els.statusBox.textContent = text || '';
    }

    function escapeHtml(str) {
      return (str || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    async function api(url, options = {}) {
      const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        ...options,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || 'Ошибка запроса');
      }
      return data;
    }

    function showLogin() {
      els.loginForm.classList.remove('hidden');
      els.registerForm.classList.add('hidden');
    }

    function showRegister() {
      els.registerForm.classList.remove('hidden');
      els.loginForm.classList.add('hidden');
    }

    function renderAuth() {
      const loggedIn = !!state.me;
      els.authBlock.classList.toggle('hidden', loggedIn);
      els.userBlock.classList.toggle('hidden', !loggedIn);
      els.dialogsPanel.classList.toggle('hidden', !loggedIn);
      els.createDialogPanel.classList.toggle('hidden', !loggedIn);
      els.composer.classList.toggle('hidden', !loggedIn || !state.activeDialogId);

      if (loggedIn) {
        els.currentUserName.textContent = state.me.display_name;
        els.currentUserLogin.textContent = '@' + state.me.login;
      }
    }

    function renderDialogs() {
      els.dialogsList.innerHTML = '';
      for (const dialog of state.dialogs) {
        const div = document.createElement('div');
        div.className = 'dialog-item' + (dialog.id === state.activeDialogId ? ' active' : '');
        div.innerHTML = `
          <div><strong>${escapeHtml(dialog.title)}</strong></div>
          <div class="muted">ID: ${dialog.id}</div>
        `;
        div.onclick = () => openDialog(dialog.id, dialog.title);
        els.dialogsList.appendChild(div);
      }
    }

    function appendMessage(msg) {
      const div = document.createElement('div');
      div.className = 'message' + (msg.sender_id === state.me?.id ? ' me' : '');
      div.innerHTML = `
        <div class="meta">${escapeHtml(msg.sender_name || ('User #' + msg.sender_id))} · ${escapeHtml(msg.created_at)}</div>
        <div>${escapeHtml(msg.body)}</div>
      `;
      els.messages.appendChild(div);
      els.messages.scrollTop = els.messages.scrollHeight;
    }

    function renderMessages(items) {
      els.messages.innerHTML = '';
      for (const item of items) appendMessage(item);
      els.messages.scrollTop = els.messages.scrollHeight;
    }

    async function refreshMe() {
      try {
        state.me = await api('/api/me');
      } catch {
        state.me = null;
      }
      renderAuth();
    }

    async function loadDialogs() {
      state.dialogs = await api('/api/dialogs');
      renderDialogs();
      ensureSocket();
      for (const dialog of state.dialogs) joinDialogRoom(dialog.id);
    }

    async function openDialog(id, title = null) {
      state.activeDialogId = id;
      renderDialogs();
      els.chatTitle.textContent = title || ('Диалог #' + id);
      els.composer.classList.remove('hidden');
      const items = await api(`/api/dialogs/${id}/messages`);
      renderMessages(items);
      joinDialogRoom(id);
    }

    function ensureSocket() {
      if (state.socket || !state.me) return;
      state.socket = io();
      state.socket.on('connect', () => setStatus('WebSocket подключен'));
      state.socket.on('message:new', (msg) => {
        const exists = state.activeDialogId === msg.dialog_id;
        if (exists) appendMessage(msg);
        loadDialogs().catch(() => {});
      });
    }

    function joinDialogRoom(dialogId) {
      if (!state.socket || state.joinedRooms.has(dialogId)) return;
      state.socket.emit('join_dialog', { dialog_id: dialogId });
      state.joinedRooms.add(dialogId);
    }

    document.getElementById('showLoginBtn').onclick = showLogin;
    document.getElementById('showRegisterBtn').onclick = showRegister;

    document.getElementById('registerBtn').onclick = async () => {
      try {
        const payload = {
          display_name: document.getElementById('registerDisplayName').value.trim(),
          login: document.getElementById('registerLogin').value.trim(),
          password: document.getElementById('registerPassword').value,
        };
        await api('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) });
        setStatus('Аккаунт создан. Теперь войди.');
        showLogin();
      } catch (e) {
        setStatus(e.message);
      }
    };

    document.getElementById('loginBtn').onclick = async () => {
      try {
        const payload = {
          login: document.getElementById('loginLogin').value.trim(),
          password: document.getElementById('loginPassword').value,
        };
        await api('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) });
        await refreshMe();
        await loadDialogs();
        setStatus('Вход выполнен');
      } catch (e) {
        setStatus(e.message);
      }
    };

    document.getElementById('logoutBtn').onclick = async () => {
      try {
        await api('/api/auth/logout', { method: 'POST' });
      } catch {}
      state.me = null;
      state.dialogs = [];
      state.activeDialogId = null;
      state.joinedRooms.clear();
      if (state.socket) {
        state.socket.disconnect();
        state.socket = null;
      }
      els.messages.innerHTML = '';
      els.chatTitle.textContent = 'Выберите диалог';
      renderAuth();
      renderDialogs();
      setStatus('Вы вышли');
    };

    document.getElementById('createDialogBtn').onclick = async () => {
      try {
        const peer_login = document.getElementById('peerLogin').value.trim();
        const dialog = await api('/api/dialogs/private', {
          method: 'POST',
          body: JSON.stringify({ peer_login })
        });
        await loadDialogs();
        await openDialog(dialog.id, dialog.title);
        setStatus('Диалог готов');
      } catch (e) {
        setStatus(e.message);
      }
    };

    document.getElementById('sendBtn').onclick = async () => {
      const body = els.messageInput.value.trim();
      if (!body || !state.activeDialogId) return;
      try {
        await api(`/api/dialogs/${state.activeDialogId}/messages`, {
          method: 'POST',
          body: JSON.stringify({ body })
        });
        els.messageInput.value = '';
      } catch (e) {
        setStatus(e.message);
      }
    };

    els.messageInput.addEventListener('keydown', async (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('sendBtn').click();
      }
    });

    async function init() {
      await refreshMe();
      if (state.me) {
        await loadDialogs();
      } else {
        showLogin();
      }
    }

    init();
  </script>
</body>
</html>
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_seen TEXT,
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dialogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL DEFAULT 'private',
            title TEXT,
            created_at TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dialog_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dialog_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            UNIQUE(dialog_id, user_id),
            FOREIGN KEY (dialog_id) REFERENCES dialogs (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dialog_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            edited_at TEXT,
            status TEXT NOT NULL DEFAULT 'sent',
            FOREIGN KEY (dialog_id) REFERENCES dialogs (id),
            FOREIGN KEY (sender_id) REFERENCES users (id)
        )
        """
    )

    conn.commit()
    conn.close()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = get_db()
    row = conn.execute(
        "SELECT id, login, display_name FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def require_user():
    user = current_user()
    if not user:
        return None, (jsonify({"error": "Требуется вход"}), 401)
    return user, None


def build_private_dialog_title(user_id, peer_id):
    conn = get_db()
    row = conn.execute(
        "SELECT display_name, login FROM users WHERE id = ?", (peer_id,)
    ).fetchone()
    conn.close()
    if not row:
        return f"Диалог #{peer_id}"
    return f"{row['display_name']} (@{row['login']})"


@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    login = (data.get("login") or "").strip()
    password = data.get("password") or ""
    display_name = (data.get("display_name") or "").strip()

    if not login or not password or not display_name:
        return jsonify({"error": "Нужны display_name, login и password"}), 400

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (login, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
            (login, generate_password_hash(password), display_name, now_str()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Логин уже существует"}), 409

    conn.close()
    return jsonify({"ok": True})


@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    login_value = (data.get("login") or "").strip()
    password = data.get("password") or ""

    conn = get_db()
    row = conn.execute(
        "SELECT id, login, password_hash, display_name FROM users WHERE login = ?",
        (login_value,),
    ).fetchone()
    conn.close()

    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Неверный логин или пароль"}), 401

    session["user_id"] = row["id"]
    return jsonify({"ok": True, "user": {"id": row["id"], "login": row["login"], "display_name": row["display_name"]}})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"error": "Не авторизован"}), 401
    return jsonify(user)


@app.get("/api/dialogs")
def list_dialogs():
    user, error = require_user()
    if error:
        return error

    conn = get_db()
    rows = conn.execute(
        """
        SELECT d.id, d.type, d.title
        FROM dialogs d
        JOIN dialog_members dm ON dm.dialog_id = d.id
        WHERE dm.user_id = ?
        ORDER BY d.id DESC
        """,
        (user["id"],),
    ).fetchall()
    conn.close()

    result = []
    for row in rows:
        title = row["title"] or f"Диалог #{row['id']}"
        result.append({"id": row["id"], "type": row["type"], "title": title})
    return jsonify(result)


@app.post("/api/dialogs/private")
def create_private_dialog():
    user, error = require_user()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    peer_login = (data.get("peer_login") or "").strip()
    if not peer_login:
        return jsonify({"error": "Нужен peer_login"}), 400

    conn = get_db()
    peer = conn.execute(
        "SELECT id, login, display_name FROM users WHERE login = ?", (peer_login,)
    ).fetchone()
    if not peer:
        conn.close()
        return jsonify({"error": "Пользователь не найден"}), 404
    if peer["id"] == user["id"]:
        conn.close()
        return jsonify({"error": "Нельзя создать диалог с самим собой"}), 400

    existing = conn.execute(
        """
        SELECT d.id, d.title
        FROM dialogs d
        JOIN dialog_members dm1 ON dm1.dialog_id = d.id
        JOIN dialog_members dm2 ON dm2.dialog_id = d.id
        WHERE d.type = 'private' AND dm1.user_id = ? AND dm2.user_id = ?
        LIMIT 1
        """,
        (user["id"], peer["id"]),
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({"id": existing["id"], "title": existing["title"] or f"{peer['display_name']} (@{peer['login']})"})

    title = f"{peer['display_name']} (@{peer['login']})"
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO dialogs (type, title, created_at, created_by) VALUES (?, ?, ?, ?)",
        ("private", title, now_str(), user["id"]),
    )
    dialog_id = cur.lastrowid
    cur.execute(
        "INSERT INTO dialog_members (dialog_id, user_id, joined_at, role) VALUES (?, ?, ?, ?)",
        (dialog_id, user["id"], now_str(), "member"),
    )
    cur.execute(
        "INSERT INTO dialog_members (dialog_id, user_id, joined_at, role) VALUES (?, ?, ?, ?)",
        (dialog_id, peer["id"], now_str(), "member"),
    )
    conn.commit()
    conn.close()

    return jsonify({"id": dialog_id, "title": title})


@app.get("/api/dialogs/<int:dialog_id>/messages")
def get_messages(dialog_id):
    user, error = require_user()
    if error:
        return error

    conn = get_db()
    member = conn.execute(
        "SELECT 1 FROM dialog_members WHERE dialog_id = ? AND user_id = ?",
        (dialog_id, user["id"]),
    ).fetchone()
    if not member:
        conn.close()
        return jsonify({"error": "Нет доступа к диалогу"}), 403

    rows = conn.execute(
        """
        SELECT m.id, m.dialog_id, m.sender_id, m.body, m.created_at, u.display_name AS sender_name
        FROM messages m
        JOIN users u ON u.id = m.sender_id
        WHERE m.dialog_id = ?
        ORDER BY m.id ASC
        """,
        (dialog_id,),
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@app.post("/api/dialogs/<int:dialog_id>/messages")
def send_message(dialog_id):
    user, error = require_user()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "Пустое сообщение"}), 400

    conn = get_db()
    member = conn.execute(
        "SELECT 1 FROM dialog_members WHERE dialog_id = ? AND user_id = ?",
        (dialog_id, user["id"]),
    ).fetchone()
    if not member:
        conn.close()
        return jsonify({"error": "Нет доступа к диалогу"}), 403

    cur = conn.cursor()
    created_at = now_str()
    cur.execute(
        "INSERT INTO messages (dialog_id, sender_id, body, created_at, status) VALUES (?, ?, ?, ?, ?)",
        (dialog_id, user["id"], body, created_at, "sent"),
    )
    message_id = cur.lastrowid
    conn.commit()
    conn.close()

    payload = {
        "id": message_id,
        "dialog_id": dialog_id,
        "sender_id": user["id"],
        "sender_name": user["display_name"],
        "body": body,
        "created_at": created_at,
        "status": "sent",
    }

    socketio.emit("message:new", payload, room=f"dialog_{dialog_id}")
    return jsonify(payload), 201


@socketio.on("join_dialog")
def ws_join_dialog(data):
    user = current_user()
    if not user:
        emit("error", {"error": "unauthorized"})
        return

    dialog_id = int((data or {}).get("dialog_id") or 0)
    if not dialog_id:
        emit("error", {"error": "bad dialog_id"})
        return

    conn = get_db()
    member = conn.execute(
        "SELECT 1 FROM dialog_members WHERE dialog_id = ? AND user_id = ?",
        (dialog_id, user["id"]),
    ).fetchone()
    conn.close()

    if not member:
        emit("error", {"error": "forbidden"})
        return

    join_room(f"dialog_{dialog_id}")
    emit("joined", {"dialog_id": dialog_id})


if __name__ == "__main__":
    init_db()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
