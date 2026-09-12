# 🤖 Jarvis AI Assistant

A powerful, fast, and customizable AI assistant built with Python, Streamlit, and Groq's high-speed inference engine. Features an interactive web UI, conversational memory, voice synthesis with multiple accents (English and Hindi), and a custom intelligence persona.

---

## ✨ Features

- **🚀 Lightning Fast Responses:** Powered by Groq API (`qwen/qwen3.8-27b`).
- **🗣️ Natural Voice Synthesis:** Integrates `edge-tts` with high-quality neural voices (British, American, and Indian English / Hindi accents).
- **🧠 Custom Identity & Persona:** Guided by a structured multi-point system prompt for accurate reasoning, math, code generation, and direct responses.
- **💬 Interactive Web UI:** Clean, modern interface built with Streamlit.
- **⚡ Token-Optimized:** Includes smart conversation pruning to stay well within free-tier API limits.

---

## 🚀 Quick Start (Local Setup)

### 1. Clone or Download this Repository
```bash
git clone https://github.com/YOUR_USERNAME/jarvis-ai.git
cd jarvis-ai
```

### 2. Set Up a Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Your API Key
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and add your free Groq API key (get one at [console.groq.com](https://console.groq.com)):
   ```env
   API_KEY=your_groq_api_key_here
   BASE_URL=https://api.groq.com/openai/v1
   MODEL_NAME=qwen/qwen3.8-27b
   ```

### 5. Launch Jarvis!
```bash
python -m streamlit run app.py
```
Open `http://localhost:8501` in your browser to chat with Jarvis.

---

## 📁 Project Structure

```
my-ai-app/
├── app.py               # Main Streamlit web application
├── voice_assistant.py   # Edge-TTS voice engine and text cleaning
├── prompt.txt           # Jarvis's system instructions and persona
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment file
└── .gitignore           # Git ignore file (keeps API keys safe)
```

---

## 🛡️ License
This project is open-source and available under the MIT License.
