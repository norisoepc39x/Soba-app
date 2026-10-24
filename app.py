import os
import requests
from moviepy import VideoFileClip
import speech_recognition as sr

def process_video_for_soba(video_path):
    print("🎬 Soba is analyzing your video file...")
    audio_path = "temp_soba_audio.wav"
    
    # 1. Extract the audio from the video clip
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path, logger=None)
    clip.close()
    
    # 2. Transcribe the audio into text data
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            transcript = recognizer.recognize_google(audio_data)
            print(f"📝 Transcribed Text: \"{transcript}\"\n")
        except Exception as e:
            transcript = "Could not extract clear speech from this clip."
            print("⚠️ Soba couldn't hear clear speech.")

    # Clean up the temporary audio file
    if os.path.exists(audio_path):
        os.remove(audio_path)
        
    # 3. Upload the text data into your local Soba AI Engine
    print("🧠 Sending data to local Soba AI Engine...")
    url = "http://localhost:11434/api/generate"
    system_prompt = (
        "You are Soba AI. Analyze this video transcript text. "
        "Tell me if this clip is engaging, pick out the key hooks, "
        "and tell me exactly how to edit it for social media."
    )
    
    payload = {
        "model": "soba",
        "prompt": f"{system_prompt}\n\nVideo Transcript: {transcript}",
        "stream": False
    }
    
    response = requests.post(url, json=payload)
    return response.json()['response']

# Run a live test! 
video_file = os.path.expanduser("~/Desktop/test_clip.mp4")

if os.path.exists(video_file):
    soba_analysis = process_video_for_soba(video_file)
    print("\n🚀 --- SOBA AI ANALYSIS --- 🚀")
    print(soba_analysis)
else:
    print(f"❌ Put a short video named 'test_clip.mp4' on your Desktop to run the test!")
