import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import closing

import requests
import streamlit as st

MODEL = "soba"
HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "soba.db")
MEDIA_DIR = os.path.join(HERE, "soba_media")


def get_ollama_url():
    # Local Ollama by default. On Streamlit Cloud, add OLLAMA_URL (your ngrok link) in the app's Secrets.
    url = os.environ.get("OLLAMA_URL")
    if not url:
        try:
            url = st.secrets.get("OLLAMA_URL")
        except Exception:
            url = None
    return (url or "http://localhost:11434").rstrip("/")


st.set_page_config(page_title="Soba", layout="wide", initial_sidebar_state="auto")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&display=swap');

:root {
  --cream: #F3ECDF; --side: #EDE4D3; --ink: #16130F; --muted: #6B5E4E;
  --line: #D9CCB6; --card: #FFFDF8; --accent: #A47A4E; --chestnut: #7A5534;
  --ease: cubic-bezier(.2, .8, .2, 1);
}
html { scroll-behavior: smooth; }
.stApp { background: var(--cream); color: var(--ink); }
.stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp label,
.stApp textarea, .stApp input, .stApp button, .stApp small { font-family: 'Sora', system-ui, sans-serif; }

/* Always readable, even when the phone or browser is in dark mode */
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li, .stApp [data-testid="stMarkdownContainer"] strong,
.stApp [data-testid="stMarkdownContainer"] em, .stApp [data-testid="stMarkdownContainer"] h1,
.stApp [data-testid="stMarkdownContainer"] h2, .stApp [data-testid="stMarkdownContainer"] h3,
.stApp [data-testid="stMarkdownContainer"] a, .stApp label { color: var(--ink) !important; }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }
header[data-testid="stHeader"] button, .stApp [data-testid="stSidebarCollapseButton"] button,
.stApp [data-testid="stExpandSidebarButton"] { color: var(--ink) !important; }

/* No grey-out flash while Soba is working */
[data-stale="true"], .stale-element { opacity: 1 !important; transition: none !important; }

/* Quiet top bar (kept, because it holds the sidebar button on phones) */
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], #MainMenu, footer { display: none !important; }

/* Centered chat column */
.block-container, [data-testid="stMainBlockContainer"] { max-width: 780px; padding-top: 3.5rem; padding-bottom: 9rem; }

/* Sidebar */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { background: var(--side) !important; }
[data-testid="stSidebar"] { border-right: 1px solid var(--line); }
.soba-brand { display: flex; align-items: center; gap: 10px; margin: 4px 0 18px; }
.soba-brand span { font-size: 21px; font-weight: 700; letter-spacing: -0.03em; color: var(--ink); }
.soba-label { font-size: 11px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin: 22px 0 8px 4px; }
.soba-empty { font-size: 13px; color: var(--muted); padding: 0 4px; }
.soba-who { font-size: 13px; color: var(--muted); margin: 26px 0 8px 4px; }
.soba-who b { color: var(--ink); }

/* Buttons */
.stButton button, .stDownloadButton button {
  min-height: 44px; border-radius: 12px; border: 1px solid var(--line); background: var(--card); color: var(--ink);
  transition: transform .18s var(--ease), box-shadow .18s var(--ease), background-color .18s var(--ease), border-color .18s var(--ease);
}
.stButton button:hover, .stDownloadButton button:hover { border-color: var(--accent); color: var(--ink); transform: translateY(-1px); box-shadow: 0 8px 20px rgba(22,19,15,.08); }
.stButton button:active, .stDownloadButton button:active { transform: translateY(0); box-shadow: none; }
.stButton button[kind="primary"], [data-testid="stBaseButton-primary"] { background: var(--ink); color: var(--cream); border-color: var(--ink); }
.stButton button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { background: #2B241D; color: var(--cream); border-color: #2B241D; }
.stFormSubmitButton button { width: 100%; min-height: 46px; border-radius: 12px; background: var(--ink) !important; border: 1px solid var(--ink) !important; }
.stApp button[kind="primary"] p, .stApp [data-testid="stBaseButton-primary"] p,
.stApp .stFormSubmitButton button p { color: var(--cream) !important; }
[data-testid="stSidebar"] .stButton button { width: 100%; }
[class*="st-key-sugg"] button { border-radius: 999px; width: 100%; font-size: 14px; }
/* Saved chats in the sidebar */
[class*="st-key-chat_"] button, [class*="st-key-cur_chat_"] button { justify-content: flex-start; text-align: left; min-height: 42px; }
[class*="st-key-chat_"] button { background: transparent; border-color: transparent; }
[class*="st-key-chat_"] button:hover { background: var(--card); border-color: var(--line); transform: none; box-shadow: none; }
[class*="st-key-cur_chat_"] button { background: var(--card); border-color: var(--accent); font-weight: 600; }
[class*="st-key-chat_"] button p, [class*="st-key-cur_chat_"] button p { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Text boxes, tabs and the sign-in card */
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"] { background: var(--card) !important; border-color: var(--line) !important; border-radius: 12px !important; }
.stApp [data-baseweb="input"] input { color: var(--ink) !important; -webkit-text-fill-color: var(--ink); caret-color: var(--ink); background: transparent !important; }
.stApp [data-testid="stForm"] { background: var(--card); border: 1px solid var(--line); border-radius: 20px; padding: 24px; }
.stApp [data-baseweb="tab"] p { font-size: 15px; font-weight: 600; }
.stApp [data-baseweb="tab-highlight"] { background-color: var(--ink) !important; }
.stApp [data-baseweb="tab-border"] { background-color: var(--line) !important; }
.stApp [data-testid="stAlertContainer"] { background-color: rgba(164,122,78,.16) !important; border-radius: 14px; }
.stApp [data-testid="stAlertContainer"] * { color: var(--ink) !important; }
.stApp [data-testid="stExpander"] details { background: var(--card) !important; border: 1px solid var(--line) !important; border-radius: 14px !important; }

/* Home */
.soba-hero { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 14px; margin: 6vh 0 28px; animation: sobaRise .5s var(--ease) both; }
.stApp .soba-hero h1 { margin: 0 !important; padding: 0 !important; font-size: 44px !important; font-weight: 300 !important; letter-spacing: -0.025em; line-height: 1.15; color: var(--ink) !important; }
.stApp .soba-hero p { margin: 0; font-size: 17px; color: var(--muted) !important; }

/* Upload box */
[data-testid="stFileUploaderDropzone"] { background: var(--card) !important; border: 1.5px dashed var(--line); border-radius: 18px;
  transition: border-color .2s var(--ease), background-color .2s var(--ease); }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent); background: #FFFFFF !important; }
[data-testid="stFileUploaderDropzone"] * { color: var(--muted) !important; }
[data-testid="stFileUploaderDropzone"] button { background: var(--card) !important; border: 1px solid var(--line) !important; border-radius: 10px; }
[data-testid="stFileUploaderDropzone"] button, [data-testid="stFileUploaderDropzone"] button * { color: var(--ink) !important; }

/* Messages: they glide in once, then stay put */
[data-testid="stChatMessage"] { background: transparent; padding: 6px 0; gap: 14px; animation: sobaRise .35s var(--ease) both; }
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { font-size: 16px; line-height: 1.65; }
[data-testid="stChatMessageAvatarAssistant"] {
  width: 2rem; height: 2rem; border-radius: 50%; box-shadow: inset 0 0 0 1px var(--line);
  background: #FFFDF8 url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120'><defs><mask id='m' maskUnits='userSpaceOnUse' x='0' y='0' width='120' height='120'><path d='M96 28H44a16 16 0 0 0 0 32h32a16 16 0 0 1 0 32H24' fill='none' stroke='white' stroke-width='22'/><path d='M96 28H44a16 16 0 0 0 0 32h32a16 16 0 0 1 0 32H24' fill='none' stroke='black' stroke-width='12'/><path d='M96 28H44a16 16 0 0 0 0 32h32a16 16 0 0 1 0 32H24' fill='none' stroke='white' stroke-width='6'/><rect x='61' y='0' width='10' height='120' fill='black'/></mask></defs><rect width='120' height='120' fill='%2316130F' mask='url(%23m)'/><rect x='64.25' y='6' width='3.5' height='112' rx='1.75' fill='%23A47A4E'/><path d='M58 0h16v6l-8 7-8-7z' fill='%23A47A4E'/></svg>") center / 62% no-repeat !important;
}
[data-testid="stChatMessageAvatarAssistant"] > * { display: none !important; }
/* Your messages: dark bubble on the right, no avatar */
[data-testid="stChatMessageAvatarUser"] { display: none !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: row !important; justify-content: flex-end !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  flex: 0 1 auto !important; width: auto !important; max-width: 80% !important; margin-left: auto !important;
  background: var(--ink); padding: 11px 18px !important; border-radius: 20px 20px 6px 20px;
  display: flex !important; align-items: center !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] * { margin: 0 !important; }
.stApp [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] p {
  color: var(--cream) !important; line-height: 1.5 !important; }
[data-testid="stChatMessage"] code { background: var(--side); color: var(--chestnut); border-radius: 6px; }
[data-testid="stChatMessage"] pre { background: var(--side) !important; border-radius: 14px; }
[data-testid="stChatMessage"] video { border-radius: 16px; }

/* Message box at the bottom */
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: var(--cream) !important; }
[data-testid="stChatInput"] { border-radius: 24px; border: 1px solid var(--line); background: var(--card) !important;
  box-shadow: 0 12px 32px rgba(22,19,15,.08); transition: border-color .2s var(--ease), box-shadow .2s var(--ease); }
[data-testid="stChatInput"] > div { background: transparent !important; }
[data-testid="stChatInput"]:focus-within { border-color: var(--accent); box-shadow: 0 16px 40px rgba(22,19,15,.12); }
[data-testid="stChatInput"] textarea { font-size: 16px; color: var(--ink) !important; -webkit-text-fill-color: var(--ink); caret-color: var(--ink); background: transparent !important; }
[data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; -webkit-text-fill-color: var(--muted); opacity: 1; }

/* The noodle: Soba's typing animation */
.soba-noodle { display: inline-flex; align-items: center; height: 28px; padding: 2px 0; }
.soba-noodle svg { overflow: hidden; }
.soba-noodle path { fill: none; stroke-width: 2.4; stroke-linecap: round; animation: noodleSlide 1.1s linear infinite; }
.soba-noodle path.n1 { stroke: var(--ink); }
.soba-noodle path.n2 { stroke: var(--accent); animation-delay: -.37s; }
.soba-noodle path.n3 { stroke: var(--ink); animation-delay: -.74s; }
@keyframes noodleSlide { from { transform: translateX(0); } to { transform: translateX(-16px); } }
@keyframes sobaRise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) {
  [data-testid="stChatMessage"], .soba-hero, .soba-noodle path { animation: none !important; }
}
</style>
""",
    unsafe_allow_html=True,
)

SOBA_MARK = """<svg viewBox="0 0 120 120" width="{size}" height="{size}" aria-hidden="true">
<defs><mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="120" height="120">
<path d="M96 28H44a16 16 0 0 0 0 32h32a16 16 0 0 1 0 32H24" fill="none" stroke="#fff" stroke-width="22"/>
<path d="M96 28H44a16 16 0 0 0 0 32h32a16 16 0 0 1 0 32H24" fill="none" stroke="#000" stroke-width="12"/>
<path d="M96 28H44a16 16 0 0 0 0 32h32a16 16 0 0 1 0 32H24" fill="none" stroke="#fff" stroke-width="6"/>
<rect x="61" y="0" width="10" height="120" fill="#000"/></mask></defs>
<rect x="0" y="0" width="120" height="120" fill="#16130F" mask="url(#{mid})"/>
<rect x="64.25" y="6" width="3.5" height="112" rx="1.75" fill="#A47A4E"/>
<path d="M58 0h16v6l-8 7-8-7z" fill="#A47A4E"/>
</svg>"""

NOODLE = """<div class="soba-noodle" role="status" aria-label="Soba is typing">
<svg viewBox="0 0 48 24" width="48" height="24" aria-hidden="true">
<path class="n1" d="M0 6 q4 -4 8 0 t8 0 t8 0 t8 0 t8 0 t8 0 t8 0 t8 0"/>
<path class="n2" d="M0 12 q4 -4 8 0 t8 0 t8 0 t8 0 t8 0 t8 0 t8 0 t8 0"/>
<path class="n3" d="M0 18 q4 -4 8 0 t8 0 t8 0 t8 0 t8 0 t8 0 t8 0 t8 0"/>
</svg></div>"""

SUGGESTIONS = [
    "Cut my podcast into 5 clips",
    "Wedding highlights, under 3 minutes",
    "Write a hook for my next video",
    "Help me plan my week",
]


# ---------------------------------------------------------------------------
# Saved accounts and chats (a small database file, soba.db, next to app.py)
# ---------------------------------------------------------------------------
def db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con


@st.cache_resource
def init_db():
    with closing(db()) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE COLLATE NOCASE NOT NULL,
            salt TEXT NOT NULL, pw_hash TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL,
            created REAL NOT NULL, updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, role TEXT NOT NULL,
            content TEXT NOT NULL, video TEXT, created REAL NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_chats_user ON chats(user_id, updated);
        CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, id);
        """)
        con.commit()
    return True


init_db()


def hash_pw(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200000).hex()


def create_user(username, password):
    salt = secrets.token_hex(16)
    try:
        with closing(db()) as con:
            cur = con.execute("INSERT INTO users (username, salt, pw_hash, created) VALUES (?, ?, ?, ?)",
                              (username, salt, hash_pw(password, salt), time.time()))
            con.commit()
            return {"id": cur.lastrowid, "username": username}
    except sqlite3.IntegrityError:
        return None


def check_user(username, password):
    with closing(db()) as con:
        row = con.execute("SELECT id, username, salt, pw_hash FROM users WHERE username = ?", (username,)).fetchone()
    if row and hmac.compare_digest(row["pw_hash"], hash_pw(password, row["salt"])):
        return {"id": row["id"], "username": row["username"]}
    return None


def list_chats(user_id):
    with closing(db()) as con:
        rows = con.execute("SELECT id, title FROM chats WHERE user_id = ? ORDER BY updated DESC LIMIT 50", (user_id,))
        return [dict(r) for r in rows]


def owns_chat(chat_id, user_id):
    with closing(db()) as con:
        return con.execute("SELECT 1 FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id)).fetchone() is not None


def create_chat(user_id, title):
    now = time.time()
    with closing(db()) as con:
        cur = con.execute("INSERT INTO chats (user_id, title, created, updated) VALUES (?, ?, ?, ?)",
                          (user_id, title, now, now))
        con.commit()
        return cur.lastrowid


def load_messages(chat_id):
    with closing(db()) as con:
        rows = con.execute("SELECT role, content, video FROM messages WHERE chat_id = ? ORDER BY id", (chat_id,))
        return [dict(r) for r in rows]


def add_message(chat_id, role, content, video=None):
    now = time.time()
    with closing(db()) as con:
        con.execute("INSERT INTO messages (chat_id, role, content, video, created) VALUES (?, ?, ?, ?, ?)",
                    (chat_id, role, content, video, now))
        con.execute("UPDATE chats SET updated = ? WHERE id = ?", (now, chat_id))
        con.commit()


def delete_chat(chat_id, user_id):
    with closing(db()) as con:
        if con.execute("SELECT 1 FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id)).fetchone() is None:
            return
        for r in con.execute("SELECT video FROM messages WHERE chat_id = ? AND video IS NOT NULL", (chat_id,)).fetchall():
            if r["video"] and os.path.exists(r["video"]):
                os.remove(r["video"])
        con.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        con.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        con.commit()


def make_title(text):
    text = " ".join(text.split())
    return text if len(text) <= 40 else text[:39] + "…"


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------
def new_chat():
    st.session_state.chat_id = None
    st.session_state.pop("pending", None)


def open_chat(chat_id):
    st.session_state.chat_id = chat_id
    st.session_state.pop("pending", None)


def queue_prompt(text):
    st.session_state.pending = text


def log_out():
    st.session_state.user = None
    st.session_state.chat_id = None
    st.session_state.pop("pending", None)


def remove_current_chat():
    user = st.session_state.get("user")
    if user and st.session_state.get("chat_id"):
        delete_chat(st.session_state.chat_id, user["id"])
    st.session_state.chat_id = None


# ---------------------------------------------------------------------------
# Talking to Soba (streams word by word from Ollama)
# ---------------------------------------------------------------------------
class SobaOffline(Exception):
    pass


def ollama_stream(history):
    msgs = [{"role": m["role"], "content": m["content"]} for m in history if m.get("content")]
    try:
        with requests.post(
            get_ollama_url() + "/api/chat",
            json={"model": MODEL, "messages": msgs, "stream": True},
            headers={"ngrok-skip-browser-warning": "1"},
            stream=True,
            timeout=(5, 180),
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if data.get("error"):
                    raise SobaOffline()
                piece = (data.get("message") or {}).get("content", "")
                if piece:
                    yield piece
                if data.get("done"):
                    break
    except (requests.exceptions.RequestException, ValueError) as e:
        raise SobaOffline() from e


def stream_reply(history):
    # The noodle wiggles until the first word arrives, then the answer types out live.
    noodle = st.empty()
    noodle.markdown(NOODLE, unsafe_allow_html=True)
    box = st.empty()
    text, last = "", 0.0
    try:
        for piece in ollama_stream(history):
            if not text:
                noodle.empty()
            text += piece
            now = time.time()
            if now - last > 0.03:
                box.markdown(text + " ▍")
                last = now
    except SobaOffline:
        if not text:
            text = ("I can't reach my brain right now. Make sure Ollama is running on the Mac, "
                    "and if you're on the website, that the Mac is connected to it.")
    noodle.empty()
    text = text.strip() or "Hmm, I didn't get an answer that time. Try asking again?"
    box.markdown(text)
    return text


# ---------------------------------------------------------------------------
# Making a first cut from an uploaded video
# ---------------------------------------------------------------------------
def make_first_cut(uploaded):
    try:
        from moviepy import VideoFileClip
    except ImportError:
        from moviepy.editor import VideoFileClip

    os.makedirs(MEDIA_DIR, exist_ok=True)
    ext = os.path.splitext(uploaded.name)[1] or ".mp4"
    src = os.path.join(MEDIA_DIR, "src_" + uuid.uuid4().hex + ext)
    out = os.path.join(MEDIA_DIR, "cut_" + uuid.uuid4().hex + ".mp4")
    with open(src, "wb") as f:
        f.write(uploaded.getbuffer())
    clip = VideoFileClip(src)
    try:
        length = min(5.0, clip.duration)
        start = max(0.0, clip.duration / 2 - length / 2)
        if hasattr(clip, "subclipped"):
            cut = clip.subclipped(start, start + length)
        else:
            cut = clip.subclip(start, start + length)
        cut.write_videofile(out, codec="libx264", audio_codec="aac", logger=None)
        cut.close()
    finally:
        clip.close()
        if os.path.exists(src):
            os.remove(src)
    return out, length


def brand():
    st.markdown('<div class="soba-brand">' + SOBA_MARK.format(size=30, mid="mSide") + "<span>Soba</span></div>",
                unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Log in / create account
# ---------------------------------------------------------------------------
def auth_screen():
    with st.sidebar:
        brand()
        st.markdown('<div class="soba-empty">Log in to see your saved chats.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="soba-hero">' + SOBA_MARK.format(size=64, mid="mAuth")
        + "<h1>Welcome to Soba</h1><p>Log in or create an account, and your chats are saved.</p></div>",
        unsafe_allow_html=True,
    )
    tab_in, tab_up = st.tabs(["Log in", "Create account"])
    with tab_in:
        with st.form("login_form"):
            u = st.text_input("Username", key="li_user")
            p = st.text_input("Password", type="password", key="li_pass")
            go = st.form_submit_button("Log in", type="primary")
        if go:
            user = check_user(u.strip(), p)
            if user:
                st.session_state.user = user
                st.session_state.chat_id = None
                st.rerun()
            else:
                st.error("That username and password don't match. Try again.")
    with tab_up:
        with st.form("signup_form"):
            u = st.text_input("Pick a username", key="su_user", help="3 to 30 letters, numbers or underscores")
            p = st.text_input("Password", type="password", key="su_pass", help="At least 6 characters")
            p2 = st.text_input("Type the password again", type="password", key="su_pass2")
            go = st.form_submit_button("Create account", type="primary")
        if go:
            u = u.strip()
            if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", u):
                st.error("Usernames can use 3 to 30 letters, numbers or underscores.")
            elif len(p) < 6:
                st.error("Use at least 6 characters for your password.")
            elif p != p2:
                st.error("Those two passwords don't match.")
            else:
                user = create_user(u, p)
                if user:
                    st.session_state.user = user
                    st.session_state.chat_id = None
                    st.rerun()
                else:
                    st.error("That username is taken. Try another one.")


user = st.session_state.get("user")
if not user:
    auth_screen()
    st.stop()

# ---------------------------------------------------------------------------
# New message (from the box at the bottom, or a suggestion button)
# ---------------------------------------------------------------------------
chat_id = st.session_state.get("chat_id")
if chat_id and not owns_chat(chat_id, user["id"]):
    chat_id = st.session_state.chat_id = None

typed = st.chat_input("Ask anything, or drop in footage to edit…")
prompt = typed or st.session_state.pop("pending", None)
if prompt:
    if not chat_id:
        chat_id = st.session_state.chat_id = create_chat(user["id"], make_title(prompt))
    add_message(chat_id, "user", prompt)

messages = load_messages(chat_id) if chat_id else []

# ---------------------------------------------------------------------------
# Sidebar: your saved chats
# ---------------------------------------------------------------------------
with st.sidebar:
    brand()
    st.button("New chat", type="primary", on_click=new_chat, key="new_chat")
    st.markdown('<div class="soba-label">Your chats</div>', unsafe_allow_html=True)
    chats = list_chats(user["id"])
    if not chats:
        st.markdown('<div class="soba-empty">Nothing yet. Say hi to Soba.</div>', unsafe_allow_html=True)
    for c in chats:
        current = c["id"] == chat_id
        st.button(c["title"], key=("cur_chat_%d" if current else "chat_%d") % c["id"], on_click=open_chat, args=(c["id"],))
    st.markdown('<div class="soba-who">Signed in as <b>' + user["username"] + "</b></div>", unsafe_allow_html=True)
    if chat_id:
        st.button("Delete this chat", on_click=remove_current_chat, key="delete_chat")
    st.button("Log out", on_click=log_out, key="log_out")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if not messages:
    st.markdown(
        '<div class="soba-hero">' + SOBA_MARK.format(size=64, mid="mHero")
        + "<h1>What do you want to make?</h1><p>Edit a video, or just ask. Soba is good at both.</p></div>",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader("Add footage", type=["mp4", "mov", "m4v", "avi"], label_visibility="collapsed")
    if uploaded is not None and st.button("Make a first cut", type="primary"):
        done = False
        with st.status("Cutting your video…", expanded=False) as status:
            try:
                out, length = make_first_cut(uploaded)
                if not chat_id:
                    chat_id = st.session_state.chat_id = create_chat(user["id"], make_title("First cut: " + uploaded.name))
                add_message(chat_id, "user", "Make a first cut of " + uploaded.name)
                add_message(chat_id, "assistant", "Here's a %d-second first cut from the middle of your clip." % round(length), out)
                status.update(label="First cut ready", state="complete")
                done = True
            except Exception as e:
                status.update(label="Couldn't cut that video", state="error")
                st.error("Something went wrong while cutting: %s" % e)
        if done:
            st.rerun()
    cols = st.columns(2)
    for i, s in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            st.button(s, key="sugg%d" % i, on_click=queue_prompt, args=(s,))
else:
    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("video"):
                if os.path.exists(m["video"]):
                    st.video(m["video"])
                    with open(m["video"], "rb") as f:
                        st.download_button("Download MP4", f, file_name="soba_first_cut.mp4",
                                           mime="video/mp4", key="dl_" + m["video"])
                else:
                    st.caption("This preview has expired. Upload the clip again to recut it.")
    if messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            reply = stream_reply(messages)
        add_message(chat_id, "assistant", reply)
