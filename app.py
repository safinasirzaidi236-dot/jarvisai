import os
import importlib
import hashlib
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import voice_assistant
importlib.reload(voice_assistant)
from voice_assistant import (
    VOICE_OPTIONS,
    generate_speech,
    transcribe_audio,
)

# 1. Load configuration from .env
load_dotenv(override=True)
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

# 2. Read custom system prompt
prompt_file = os.path.join(os.path.dirname(__file__), "prompt.txt")
if os.path.exists(prompt_file):
    with open(prompt_file, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
else:
    SYSTEM_PROMPT = "You are Jarvis, a highly capable AI assistant."

# 3. Setup Groq / OpenAI Client
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# 4. Streamlit Web Page Config
st.set_page_config(
    page_title="Jarvis AI - Voice & Chat Assistant",
    page_icon="🎙️",
    layout="centered"
)

# Custom HUD-inspired styling
st.markdown("""
<style>
    .jarvis-header {
        text-align: center;
        padding-bottom: 0.5rem;
    }
    .jarvis-status {
        display: inline-block;
        background: rgba(0, 210, 255, 0.1);
        border: 1px solid rgba(0, 210, 255, 0.3);
        border-radius: 12px;
        padding: 4px 14px;
        font-size: 0.85rem;
        color: #00d2ff;
        margin-bottom: 1rem;
    }
    .stAudio {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 5. Sidebar Controls
with st.sidebar:
    st.title("⚙️ Jarvis Settings")
    
    st.subheader("🎙️ Voice Output")
    voice_mode = st.radio(
        "Response Mode",
        options=[
            "🎙️ Adaptive (Oral for voice, Written for text)",
            "🔊 Always Speak (Voice for all queries)",
            "🔇 Mute (Written only for all queries)"
        ],
        index=0,
        help="• Adaptive: Jarvis answers orally when you speak, and in written form when you type.\n• Always Speak: Jarvis speaks every response aloud.\n• Mute: Written text responses only."
    )
    
    selected_voice_name = st.selectbox(
        "Voice Persona",
        options=list(VOICE_OPTIONS.keys()),
        index=0,
        help="Select Jarvis's voice accent and personality"
    )
    voice_identifier = VOICE_OPTIONS[selected_voice_name]
    
    speed_offset = st.slider(
        "Speech Speed",
        min_value=-20,
        max_value=30,
        value=0,
        step=5,
        format="%d%%",
        help="Adjust voice talking speed"
    )
    voice_rate = f"{'+' if speed_offset >= 0 else ''}{speed_offset}%"

    pitch_offset = st.slider(
        "Voice Pitch (Masculine / Deep)",
        min_value=-15,
        max_value=10,
        value=-4,
        step=1,
        format="%dHz",
        help="Lower pitch gives Jarvis a deeper, more masculine resonance"
    )
    voice_pitch = f"{'+' if pitch_offset >= 0 else ''}{pitch_offset}Hz"
    
    st.divider()
    st.subheader("🎧 Speech-to-Text")
    whisper_model = st.selectbox(
        "Transcription Model",
        options=["whisper-large-v3-turbo", "whisper-large-v3"],
        index=0,
        help="Groq Whisper model for audio transcription"
    )

    transcription_lang_choice = st.selectbox(
        "Voice Input Language",
        options=["Auto-Detect (English / Hindi)", "Hindi (हिन्दी)", "English"],
        index=0,
        help="Language spoken into the microphone"
    )
    whisper_lang = {
        "Auto-Detect (English / Hindi)": None,
        "Hindi (हिन्दी)": "hi",
        "English": "en"
    }[transcription_lang_choice]

    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.last_processed_audio = None
        st.session_state.latest_audio = None
        st.session_state.audio_key = st.session_state.get("audio_key", 0) + 1
        st.rerun()

# 6. Initialize conversation history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

if "latest_audio" not in st.session_state:
    st.session_state.latest_audio = None

if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0

# Header Display
if voice_mode.startswith("🔇"):
    status_text = "○ VOICE MUTED (WRITTEN ONLY)"
elif voice_mode.startswith("🔊"):
    status_text = "● CONTINUOUS VOICE ONLINE"
else:
    status_text = "● ADAPTIVE MODE ONLINE (ORAL FOR VOICE, WRITTEN FOR TEXT)"

st.markdown(f"""
<div class="jarvis-header">
    <h1>🤖 JARVIS</h1>
    <span class="jarvis-status">{status_text}</span>
</div>
""", unsafe_allow_html=True)

# 7. Voice Input Section (Microphone)
with st.expander("🎙️ Tap here to speak to Jarvis", expanded=True):
    audio_val = st.audio_input(
        "Record voice query",
        key=f"voice_mic_{st.session_state.audio_key}",
        label_visibility="collapsed"
    )

# Check if a new voice recording was received
voice_user_input = None
if audio_val is not None:
    audio_bytes = audio_val.getvalue()
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_processed_audio != audio_hash:
        st.session_state.last_processed_audio = audio_hash
        with st.spinner("🎧 Jarvis is listening & transcribing..."):
            try:
                transcription = transcribe_audio(client, audio_bytes, model=whisper_model, language=whisper_lang)
                if transcription:
                    voice_user_input = transcription
            except Exception as e:
                st.error(f"Voice transcription error: {e}")

# 8. Text Input Section
text_user_input = st.chat_input("Type your message (English / हिंदी) or speak into the microphone above...")

# Determine active user input (voice has priority if fresh audio recorded)
active_input = voice_user_input or text_user_input
input_is_voice = bool(voice_user_input)

# 9. Display past messages
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                if msg.get("is_voice"):
                    st.markdown(f"🎙️ *\"{msg['content']}\"*")
                else:
                    st.markdown(msg["content"])
            else:
                st.markdown(msg["content"])
                # If assistant message has pre-generated audio, display replay player
                if msg.get("audio"):
                    st.audio(msg["audio"], format="audio/mp3")

# 10. Handle New User Message
if active_input:
    # Determine if response should be oral (spoken aloud) based on active mode & input type
    if voice_mode.startswith("🎙️ Adaptive"):
        should_speak = input_is_voice
    elif voice_mode.startswith("🔊 Always"):
        should_speak = True
    else:  # Mute
        should_speak = False

    # Append & display user message
    user_display = f"🎙️ *\"{active_input}\"*" if input_is_voice else active_input
    st.session_state.messages.append({
        "role": "user",
        "content": active_input,
        "is_voice": input_is_voice
    })
    with st.chat_message("user"):
        st.markdown(user_display)

    # Stream the AI's response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Keep system prompt + recent messages to stay within free-tier context
            system_msg = [st.session_state.messages[0]]
            recent_conversation = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[1:]
            ][-6:]

            # Provide modality context instruction to the model
            if input_is_voice:
                modality_hint = {
                    "role": "system",
                    "content": "The user is speaking to you orally. Give a natural, conversational, and direct spoken response suitable for listening aloud. Avoid unnecessary markdown syntax, bullets, or raw code dumps unless explicitly asked."
                }
            else:
                modality_hint = {
                    "role": "system",
                    "content": "The user wrote this question. Provide your response in written form with clear markdown formatting, headings, bullet points, or code blocks where appropriate."
                }
            payload_messages = [system_msg[0], modality_hint] + recent_conversation

            # Call the model with streaming
            response_stream = client.chat.completions.create(
                model=model_name,
                messages=payload_messages,
                max_tokens=700,
                stream=True
            )

            for chunk in response_stream:
                content = chunk.choices[0].delta.content or ""
                full_response += content
                message_placeholder.markdown(full_response + "▌")
                
            message_placeholder.markdown(full_response)
            
            # Generate and play voice response only when oral mode is triggered
            spoken_audio = None
            if should_speak and full_response:
                with st.spinner("🔊 Jarvis is speaking..."):
                    try:
                        try:
                            spoken_audio = generate_speech(
                                full_response,
                                voice=voice_identifier,
                                rate=voice_rate,
                                pitch=voice_pitch
                            )
                        except TypeError:
                            spoken_audio = generate_speech(
                                full_response,
                                voice=voice_identifier,
                                rate=voice_rate
                            )
                        if spoken_audio:
                            st.audio(spoken_audio, format="audio/mp3", autoplay=True)
                    except Exception as ve:
                        st.caption(f"⚠️ Voice generation notice: {ve}")

            # Save the assistant's response and generated audio to session history
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "audio": spoken_audio
            })

        except Exception as e:
            message_placeholder.error(f"Rate limit or API issue: {e}")