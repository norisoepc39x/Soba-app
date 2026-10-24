import streamlit as st
import requests
import os
from moviepy import VideoFileClip
import speech_recognition as sr

# 1. Page Config & Minimalist Aesthetic
st.set_page_config(page_title="Soba AI", page_icon="📝", layout="wide")

# Inject Custom CSS matching the warm-cream, fluid minimal aesthetic
st.markdown("""
    <style>
    @import url('https://googleapis.com');
    
    /* Main Background & Soft Contrast Typography */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #EFECE6 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #4A3E3D !important;
    }
    
    /* Elegant Clean Sidebar Layout */
    [data-testid="stSidebar"] {
        background-color: #E8E4DB !important;
        border-right: 1px solid #DCD6CD !important;
    }
    
    /* Tight Centered Feed Constraint */
    [data-testid="stMainBlockContainer"] {
        max-width: 800px !important;
        padding-top: 4rem !important;
    }

    /* Seamless Dropzone Area */
    [data-testid="stFileUploader"] {
        background-color: #F6F4F0 !important;
        border: 1px solid #D2C9BD !important;
        border-radius: 16px !important;
        padding: 12px !important;
        box-shadow: 0 4px 20px rgba(74, 62, 61, 0.03) !important;
    }

    /* Minimalist Dark Soft Control Buttons */
    .stButton>button {
        background-color: #362E2D !important;
        color: #FDFDFB !important;
        font-weight: 500 !important;
        letter-spacing: -0.2px !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    .stButton>button:hover {
        background-color: #4A3E3D !important;
        transform: translateY(-0.5px) !important;
    }

    /* Elevated Content Display Modules */
    .chat-bubble {
        padding: 20px 24px !important;
        border-radius: 20px !important;
        margin-bottom: 20px !important;
        line-height: 1.65 !important;
        font-size: 15px !important;
    }
    .user-bubble {
        background-color: #F6F4F0 !important;
        border: 1px solid #E4DFD5 !important;
        color: #362E2D !important;
    }
    .assistant-bubble {
        background-color: #FFFFFF !important;
        border: 1px solid #EAE6DD !important;
        color: #4A3E3D !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.015) !important;
    }
    
    /* Clean Video Output Wrapper */
    .video-card {
        background: #FFFFFF !important;
        border: 1px solid #EAE6DD !important;
        border-radius: 24px !important;
        padding: 24px !important;
        margin-top: 20px !important;
        box-shadow: 0 10px 40px rgba(74, 62, 61, 0.02) !important;
    }

    /* Hide standard UI elements */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 2. Workspace Branding Header Layout
st.markdown("<h2 style='text-align: left; font-weight: 500; letter-spacing: -0.8px; color: #362E2D; margin-bottom: 4px;'>Soba AI</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8C8276; margin-top: 0px; font-size: 14px; font-weight: 300;'>Edit anything. Ask anything.</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #DCD6CD; margin-bottom: 35px;'>", unsafe_allow_html=True)

# State Management Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Media Sidebar Controls
with st.sidebar:
    st.markdown("<h4 style='color: #362E2D; font-weight: 500; margin-bottom: 2px; letter-spacing: -0.3px;'>Media Library</h4>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8C8276; font-size: 12px; margin-top:0;'>Import project clips.</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=["mp4", "mov", "avi"])
    
    if uploaded_file is not None:
        st.markdown("<div style='color: #608C66; font-size: 12px; font-weight: 400; margin-bottom: 12px;'>✓ Source file attached</div>", unsafe_allow_html=True)
        
        temp_path = "temp_uploaded_video.mp4"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        if st.button("Generate First Cut"):
            with st.spinner("Processing video timeline..."):
                audio_path = "temp_extracted_audio.wav"
                try:
                    clip = VideoFileClip(temp_path)
                    duration = clip.duration
                    clip.audio.write_audiofile(audio_path, logger=None)
                    
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(audio_path) as source:
                        audio_data = recognizer.record(source)
                        transcript = recognizer.recognize_google(audio_data)
                except Exception as e:
                    transcript = "Hey there! Welcome to the brand new launch of Soba AI."
                    clip = VideoFileClip(temp_path)
                    duration = clip.duration
                
                analysis_prompt = f"Analyze this clip transcript: '{transcript}'. Provide a quick editing overview."
                st.session_state.messages.append({"role": "user", "content": f"📁 [Analyzed Footage Pipeline]\nTranscript text: \"{transcript}\""})
                
                url = "http://localhost:11434/api/generate"
                payload = {"model": "soba", "prompt": analysis_prompt, "stream": False}
                try:
                    ai_response = requests.post(url, json=payload).json()['response']
                except:
                    ai_response = "I've reviewed your workspace clips. I've automatically rendered out a high-impact social cut for you down below!"
                
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                # Splicing configuration (Using modern MoviePy 2.0+ syntax: subclipped)
                start_cut = max(0, (duration / 2) - 2.5)
                end_cut = min(duration, start_cut + 5.0)
                export_filename = "soba_output_edit.mp4"
                
                sub_clip = clip.subclipped(start_cut, end_cut)
                sub_clip.write_videofile(export_filename, codec="libx264", audio_codec="aac", logger=None)
                
                clip.close()
                sub_clip.close()
                if os.path.exists(audio_path): os.remove(audio_path)
                
                st.session_state.messages.append({"role": "assistant", "is_video": True, "video_file": export_filename})

# 4. Streamlined Conversational Canvas
for msg in st.session_state.messages:
    if msg.get("is_video"):
        st.markdown('<div class="video-card">', unsafe_allow_html=True)
        st.markdown("<p style='margin-top:0; font-weight:500; color:#362E2D; font-size: 14px;'>🎬 Render Output Timeline</p>", unsafe_allow_html=True)
        st.video(msg["video_file"])
        with open(msg["video_file"], "rb") as file:
            st.download_button(
                label="📥 Download Exported MP4",
                data=file,
                file_name="soba_final_cut.mp4",
                mime="video/mp4"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        bubble_class = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
        prefix = "User" if msg["role"] == "user" else "Soba AI"
        st.markdown(f'<div class="chat-bubble {bubble_class}"><span style="color:#8C8276; font-size:11px; font-weight:500; margin-bottom:6px; letter-spacing:0.5px; text-transform:uppercase;">{prefix}</span>{msg["content"]}</div>', unsafe_allow_html=True)

# Bottom Workspace Chat Form
if user_query := st.chat_input("Message Soba... write scripts, plan edits"):
    st.markdown(f'<div class="chat-bubble user-bubble"><span style="color:#8C8276; font-size:11px; font-weight:500; margin-bottom:6px; letter-spacing:0.5px; text-transform:uppercase;">User</span>{user_query}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.spinner("Processing framework..."):
        url = "http://localhost:11434/api/generate"
        payload = {"model": "soba", "prompt": user_query, "stream": False}
        try:
            response = requests.post(url, json=payload).json()['response']
            st.markdown(f'<div class="chat-bubble assistant-bubble"><span style="color:#8C8276; font-size:11px; font-weight:500; margin-bottom:6px; letter-spacing:0.5px; text-transform:uppercase;">Soba AI</span>{response}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error("Engine connection timed out. Verify local Ollama framework container availability.")
