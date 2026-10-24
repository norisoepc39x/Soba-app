import json
import os
import tempfile
import time
import uuid

import requests
import streamlit as st

MODEL = "soba"


def get_ollama_url():
    # Local Ollama by default. On the website, add OLLAMA_URL (your ngrok link) in the app's Secrets.
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

/* No grey-out flash while Soba is working */
[data-stale="true"], .stale-element { opacity: 1 !important; transition: none !important; }

/* Quiet top bar (kept, because it holds the sidebar button on phones) */
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], #MainMenu, footer { display: none !important; }

/* Centered chat column */
.block-container, [data-testid="stMainBlockContainer"] { max-width: 780px; padding-top: 3.5rem; padding-bottom: 9rem; }

/* Sidebar */
[data-testid="stSidebar"] { background: var(--side); border-right: 1px solid var(--line); }
.soba-brand { display: flex; align-items: center; gap: 10px; margin: 4px 0 18px; }
.soba-brand span { font-size: 21px; font-weight: 700; letter-spacing: -0.03em; color: var(--ink); }
.soba-label { font-size: 11px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin: 22px 0 8px 4px; }
.soba-item { padding: 11px 12px; border-radius: 12px; font-size: 14px; color: var(--ink); background: var(--card);
  box-shadow: inset 0 0 0 1px var(--line); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.soba-empty { font-size: 13px; color: var(--muted); padding: 0 4px; }

/* Buttons */
.stButton button, .stDownloadButton button {
  min-height: 44px; border-radius: 12px; border: 1px solid var(--line); background: var(--card); color: var(--ink);
  transition: transform .18s var(--ease), box-shadow .18s var(--ease), background-color .18s var(--ease), border-color .18s var(--ease);
}
.stButton button:hover, .stDownloadButton button:hover { border-color: var(--accent); color: var(--ink); transform: translateY(-1px); box-shadow: 0 8px 20px rgba(22,19,15,.08); }
.stButton button:active, .stDownloadButton button:active { transform: translateY(0); box-shadow: none; }
.stButton button[kind="primary"], [data-testid="stBaseButton-primary"] { background: var(--ink); color: var(--cream); border-color: var(--ink); }
.stButton button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { background: #2B241D; color: var(--cream); border-color: #2B241D; }
[data-testid="stSidebar"] .stButton button { width: 100%; }
[class*="st-key-sugg"] button { border-radius: 999px; width: 100%; font-size: 14px; }

/* Home */
.soba-hero { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 14px; margin: 6vh 0 28px; animation: sobaRise .5s var(--ease) both; }
.stApp .soba-hero h1 { margin: 0 !important; padding: 0 !important; font-size: 44px !important; font-weight: 300 !important; letter-spacing: -0.025em; line-height: 1.15; color: var(--ink); }
.stApp .soba-hero p { margin: 0; font-size: 17px; color: var(--muted); }

/* Upload box */
[data-testid="stFileUploaderDropzone"] { background: var(--card); border: 1.5px dashed var(--line); border-radius: 18px;
  transition: border-color .2s var(--ease), background-color .2s var(--ease); }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent); background: #FFFFFF; }

/* Messages: they glide in once, then stay put */
[data-testid="stChatMessage"] { background: transparent; padding: 6px 0; gap: 14px; animation: sobaRise .35s var(--ease) both; }
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { font-size: 16px; line-height: 1.65; }
[data-testid="stChatMessageAvatarAssistant"] {
  width: 2rem; height: 2rem; border-radius: 50%; box-shadow: inset 0 0 0 1px var(--line);
  background: #FFFDF8 url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120'><defs><mask id='m' maskUnits='userSpaceOnUse' x='0' y='0' width='120' height='120'><path d='M96 28H44a16 16 0 0 0 0 32h32a16 16 0 0 1 0 32H24' fill='none' stroke='white' stroke-width='22'/><path d='M96 28H44a16 16 0 0 0 0 32h32a16 16 0 0 1 0 32H24' fill='none' stroke='black' stroke-width='12'/><path d='M96 28H44a16 16 0 0 0 0 32h32a16 16 0 0 1 0 32H24' fill='none' stroke='white' stroke-width='6'/><rect x='61' y='0' width='10' height='120' fill='black'/></mask></defs><rect width='120' height='120' fill='%2316130F' mask='url(%23m)'/><rect x='64.25' y='6' width='3.5' height='112' rx='1.75' fill='%23A47A4E'/><path d='M58 0h16v6l-8 7-8-7z' fill='%23A47A4E'/></svg>") center / 62% no-repeat !important;
}
[data-testid="stChatMessageAvatarAssistant"] > * { display: none !important; }
/* Your messages: dark bubble on the right, no avatar */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: row-reverse; }
[data-testid="stChatMessageAvatarUser"] { display: none !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  flex: 0 1 auto; max-width: 80%; background: var(--ink); padding: 12px 18px; border-radius: 20px 20px 6px 20px; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] p { color: var(--cream); margin: 0; }
[data-testid="stChatMessage"] code { background: var(--side); color: var(--chestnut); border-radius: 6px; }
[data-testid="stChatMessage"] pre { background: var(--side) !important; border-radius: 14px; }
[data-testid="stChatMessage"] video { border-radius: 16px; }

/* Message box at the bottom */
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: var(--cream); }
[data-testid="stChatInput"] { border-radius: 24px; border: 1px solid var(--line); background: var(--card);
  box-shadow: 0 12px 32px rgba(22,19,15,.08); transition: border-color .2s var(--ease), box-shadow .2s var(--ease); }
[data-testid="stChatInput"]:focus-within { border-color: var(--accent); box-shadow: 0 16px 40px rgba(22,19,15,.12); }
[data-testid="stChatInput"] textarea { font-size: 16px; }

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

if "messages" not in st.session_state:
    st.session_state.messages = []


def new_chat():
    st.session_state.messages = []
    st.session_state.pop("pending", None)


def queue_prompt(text):
    st.session_state.pending = text


class SobaOffline(Exception):
    pass


def ollama_stream(history):
    msgs = [{"role": m["role"], "content": m["content"]} for m in history if m.get("content")]
    try:
        with requests.post(
            get_ollama_url() + "/api/chat",
            json={"model": MODEL, "messages": msgs, "stream": True},
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
                    "and if you're on the website, that your ngrok link is saved as OLLAMA_URL.")
    noodle.empty()
    text = text.strip() or "Hmm, I didn't get an answer that time. Try asking again?"
    box.markdown(text)
    return text


def make_first_cut(uploaded):
    try:
        from moviepy import VideoFileClip
    except ImportError:
        from moviepy.editor import VideoFileClip

    tmp = tempfile.gettempdir()
    ext = os.path.splitext(uploaded.name)[1] or ".mp4"
    src = os.path.join(tmp, "soba_src_" + uuid.uuid4().hex + ext)
    out = os.path.join(tmp, "soba_cut_" + uuid.uuid4().hex + ".mp4")
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


# New message: from the box at the bottom, or a suggestion button
typed = st.chat_input("Ask anything, or drop in footage to edit…")
prompt = typed or st.session_state.pop("pending", None)
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

# Sidebar
with st.sidebar:
    st.markdown('<div class="soba-brand">' + SOBA_MARK.format(size=30, mid="mSide") + "<span>Soba</span></div>",
                unsafe_allow_html=True)
    st.button("New chat", type="primary", on_click=new_chat)
    st.markdown('<div class="soba-label">This chat</div>', unsafe_allow_html=True)
    first = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), None)
    if first:
        title = first if len(first) <= 34 else first[:33] + "…"
        st.markdown('<div class="soba-item">' + title.replace("<", "&lt;") + "</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="soba-empty">Nothing yet. Say hi to Soba.</div>', unsafe_allow_html=True)

# Main
if not st.session_state.messages:
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
                st.session_state.messages.append({"role": "user", "content": "Make a first cut of " + uploaded.name})
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Here's a %d-second first cut from the middle of your clip." % round(length),
                    "video": out,
                })
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
    for m in st.session_state.messages:
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
    if st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            reply = stream_reply(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# Fix: your messages sit on the right, with the text fully inside the bubble
st.markdown("""
<style>
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  flex-direction: row !important; justify-content: flex-end !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  flex: 0 1 auto !important; width: auto !important; max-width: 80% !important; margin-left: auto !important;
  padding: 11px 18px !important; display: flex !important; align-items: center !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] * {
  margin: 0 !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] p {
  line-height: 1.5 !important; }
</style>
""", unsafe_allow_html=True)
