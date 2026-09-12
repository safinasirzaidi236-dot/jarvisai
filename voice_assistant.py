import re
import asyncio
import io
import edge_tts

# Preset voices available for Jarvis
VOICE_OPTIONS = {
    "Jarvis (Deep British Male)": "en-GB-ThomasNeural",
    "Jarvis Hindi (Madhur Male)": "hi-IN-MadhurNeural",
    "Jarvis Hindi (Swara Female)": "hi-IN-SwaraNeural",
    "Jarvis Classic (British Male)": "en-GB-RyanNeural",
    "Brian (Deep US Male)": "en-US-BrianNeural",
    "Christopher (Authoritative US Male)": "en-US-ChristopherNeural",
    "Guy (US Male)": "en-US-GuyNeural",
    "Prabhat (Indian English Male)": "en-IN-PrabhatNeural",
    "Aria (US Female)": "en-US-AriaNeural",
    "Sonia (British Female)": "en-GB-SoniaNeural",
    "Neerja (Indian English Female)": "en-IN-NeerjaNeural",
}

def clean_text_for_speech(text: str, max_chars: int = 1200) -> str:
    """
    Cleans markdown formatting, code blocks, URLs, and symbols
    so that the text sounds natural and fluent when spoken aloud.
    """
    if not text:
        return ""

    # Replace fenced code blocks with a brief spoken note
    cleaned = re.sub(r'```[\s\S]*?```', ' [Code block omitted] ', text)

    # Remove inline code backticks
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)

    # Replace markdown links [label](url) with just label
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)

    # Remove bare URLs
    cleaned = re.sub(r'https?://\S+', '', cleaned)

    # Remove LaTeX math blocks $$...$$ and inline $...$
    cleaned = re.sub(r'\$\$[\s\S]*?\$\$', ' [Formula] ', cleaned)
    cleaned = re.sub(r'\$([^\$]+)\$', r'\1', cleaned)

    # Remove markdown headers (#, ##, etc.), bullets (*, -, >)
    cleaned = re.sub(r'^[#*>\-+\s]+', '', cleaned, flags=re.MULTILINE)

    # Remove bold / italic markers (**word**, *word*, __word__)
    cleaned = re.sub(r'[*_]{1,3}([^*_]+)[*_]{1,3}', r'\1', cleaned)

    # Remove horizontal rules
    cleaned = re.sub(r'[-*_]{3,}', ' ', cleaned)

    # Replace consecutive newlines and whitespace with a single space or pause
    cleaned = re.sub(r'\n+', '. ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Limit to max_chars to avoid excessively long audio reads
    if len(cleaned) > max_chars:
        # Check standard punctuation and Hindi poorna viraam '।'
        cut_point = max(
            cleaned.rfind('. ', 0, max_chars),
            cleaned.rfind('। ', 0, max_chars),
            cleaned.rfind('।', 0, max_chars),
            cleaned.rfind('? ', 0, max_chars),
            cleaned.rfind('! ', 0, max_chars)
        )
        if cut_point > 0:
            cleaned = cleaned[:cut_point + 1]
        else:
            cleaned = cleaned[:max_chars].rstrip() + "..."

    return cleaned


def is_hindi_text(text: str) -> bool:
    """
    Detects if the given text contains Devanagari script (Hindi characters).
    """
    return bool(re.search(r'[\u0900-\u097F]', text))


async def _generate_speech_async(text: str, voice: str = "en-GB-ThomasNeural", rate: str = "+0%", pitch: str = "-4Hz", **kwargs) -> bytes:
    """
    Asynchronously synthesizes speech using Microsoft Edge Neural TTS.
    Intelligently routes Devanagari Hindi text to a native Hindi neural voice.
    """
    effective_voice = voice
    if is_hindi_text(text) and not voice.startswith("hi-"):
        # Select female or male Hindi voice depending on current persona
        if any(female in voice.lower() for female in ["female", "aria", "sonia", "neerja", "swara"]):
            effective_voice = "hi-IN-SwaraNeural"
        else:
            effective_voice = "hi-IN-MadhurNeural"

    communicate = edge_tts.Communicate(text=text, voice=effective_voice, rate=rate, pitch=pitch)
    audio_stream = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])
    return audio_stream.getvalue()


def generate_speech(text: str, voice: str = "en-GB-ThomasNeural", rate: str = "+0%", pitch: str = "-4Hz", **kwargs) -> bytes:
    """
    Synchronous wrapper to generate neural speech bytes (MP3).
    Safe to invoke inside Streamlit execution contexts.
    """
    clean_text = clean_text_for_speech(text)
    if not clean_text:
        return b""

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                result = pool.submit(asyncio.run, _generate_speech_async(clean_text, voice, rate, pitch, **kwargs)).result()
            return result
        else:
            return loop.run_until_complete(_generate_speech_async(clean_text, voice, rate, pitch, **kwargs))
    except RuntimeError:
        return asyncio.run(_generate_speech_async(clean_text, voice, rate, pitch, **kwargs))


def transcribe_audio(client, audio_data, model: str = "whisper-large-v3-turbo", language: str = None, **kwargs) -> str:
    """
    Transcribes audio bytes or file-like object using Groq's Whisper model.
    Supports optional language hints (e.g. 'hi' for Hindi, 'en' for English).
    """
    if hasattr(audio_data, "read"):
        content = audio_data.read()
        filename = getattr(audio_data, "name", "audio.wav")
    elif isinstance(audio_data, bytes):
        content = audio_data
        filename = "audio.wav"
    else:
        raise ValueError("Unsupported audio data format")

    if not content:
        return ""

    audio_file = (filename, content, "audio/wav")
    transcribe_params = {
        "model": model,
        "file": audio_file,
        "response_format": "text"
    }
    if language:
        transcribe_params["language"] = language

    transcription = client.audio.transcriptions.create(**transcribe_params)
    return transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
