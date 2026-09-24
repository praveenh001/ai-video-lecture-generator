# Synapse AI - AI-Powered Video Lecture Generator 🎓🎬

A full-stack, autonomous educational video lecture generation platform built with **Python**, **FastAPI**, and a **modern 60FPS dynamic visual canvas frontend**.

Synapse AI thinks like an experienced teacher, instructional designer, animator, and video producer—turning any topic into an instructional, animated educational masterclass with natural neural narration, synchronized animations, readable subtitles, and complete study packages.

---

## 🌟 Key Features

### 1. Pedagogical Topic Analysis & Clarification
- **Domain Intelligence**: Automatically detects domain (*Computer Science*, *Mathematics*, *Natural Sciences*, *Software Engineering*, *General Knowledge*).
- **Adaptive Clarification**: Asks intelligent clarification questions when appropriate:
  - Knowledge Level (*Beginner*, *Intermediate*, *Advanced*)
  - Learning Purpose (*Coding Interview*, *Academic Exam*, *Practical Engineering*, *Conceptual Intuition*)
  - Visual Teaching Style (*Algorithm & Array Simulator*, *Code Execution & Call Stack*, *Mathematical Curves*, *Visual Metaphor*)
  - Lecture Duration (*Quick 2-3 mins*, *Standard 4-5 mins*, *Comprehensive 7-9 mins*)
  - AI Narrator Persona (*Christopher, Jenny, Guy, Sonia, Aria, Eric*)

### 2. Multi-Domain Dynamic Animation Engine (Not Just Static Slides!)
- **Algorithm & Data Structure Animator**:
  - Live array rendering with rounded cards, pointer badges (`LOW`, `MID`, `HIGH`), active comparison banner (`16 < 23 -> Discard Left Half`), search space elimination, and glowing target match beacons.
- **Code Execution & Variable Watch Visualizer**:
  - Syntax-highlighted code editor with macOS dots, line-by-line execution pointer (`▶`), and live variable scope inspector.
- **Mathematical Curves & Tangents**:
  - Cartesian coordinate system, plotted curve $f(x) = x^2$, moving point $(x_0, f(x_0))$, and dynamic secant lines pivoting into tangent lines as $h \to 0$ with instantaneous slope calculation.
- **Process Simulation & Flow Diagrams**:
  - Multi-stage pipeline with pulsating active states and animated energy packets.
- **Concept Metaphor & Comparison Matrix**:
  - Contrasting side-by-side cards comparing intuitive analogies to technical realities.

### 3. Natural AI Narration & Audio Synchronization
- High-fidelity neural voiceover using Microsoft Neural Voices (`edge-tts`).
- Word/sentence boundary capture for exact timestamp synchronization.
- Automatic **WebVTT** (`.vtt`) subtitle generation with chapter cues.
- Integrated ambient lo-fi / study background music with gentle audio ducking.

### 4. Dual-Mode Cinema Player
- **Mode A: 60FPS Dynamic Interactive Canvas Player**:
  - Real-time HTML5 Canvas animation engine synchronized with neural voiceover audio.
  - Zero-wait instantaneous playback.
- **Mode B: Server-Rendered Full HD MP4 Video**:
  - Background/On-demand video rendering pipeline using **FFmpeg** (`imageio-ffmpeg`) that renders HD frames, stitches scenes, and mixes audio with background music.
- **Player Controls**:
  - Play/Pause (Spacebar shortcut), Timeline scrubber with chapter ticks and hover preview, speed selector (0.75x to 2x), subtitle toggle ([CC]), ambient music toggle (🎵), and fullscreen.
  - **Synchronized Transcript**: Real-time glowing cue highlight; clicking any sentence immediately seeks playback to that exact moment.
  - **Chapters Drawer**: Jump between pedagogical phases (*Hook*, *Foundation*, *Visual Demonstration*, *Edge Cases*, *Summary*).

### 5. Comprehensive Learning Materials Hub
- 📑 **Lecture Notes**: Complete markdown study notes with definitions, formulas, and code.
- 💡 **Key Concepts**: Grid of cards with definitions and importance badges.
- 🎯 **Interactive Quiz**: Multiple choice questions with instant validation and detailed explanations.
- 🃏 **3D Flashcards**: Flip cards with category tags, front/back views, and a "Mark Mastered" progress counter.
- 🧪 **Practice Problems**: Real-world interview / exam problems with hints and toggleable step-by-step solutions.

### 6. Scene Studio & In-Place Regeneration
- Inspect every scene's chapter title, narration script, visual animation type, and duration.
- In-place editor: Edit script text or change visual type, click **"Regenerate Scene"**, and the backend re-synthesizes speech, recalculates timestamps, and refreshes the lecture in seconds!

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn, Pydantic, Jinja2
- **Audio & TTS**: `edge-tts` (Microsoft Neural Voices), FFmpeg audio mixing
- **Video Rendering**: `imageio-ffmpeg` (bundled FFmpeg 7.1), Pillow (HD frame rasterization)
- **AI & Reasoning**: Pluggable architecture supporting Google Gemini API (`google-generativeai`) + rich built-in pedagogical curriculum blueprints for Computer Science, Math, Science, and general topics
- **Frontend**: HTML5, Modern Vanilla CSS (Design system, glassmorphism, dark theme), Canvas 2D 60FPS Animation Engine, Vanilla JavaScript ES6+

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install fastapi uvicorn pydantic jinja2 pillow numpy requests aiohttp edge-tts imageio-ffmpeg google-generativeai
```

### 2. Launch the Application
```bash
python run.py
```
Open your browser at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📂 Project Structure

```
├── backend/
│   ├── main.py                  # FastAPI application & API endpoints
│   ├── models.py                # Pydantic schemas for lectures, scenes, quiz, flashcards
│   ├── services/
│   │   ├── ai_engine.py         # Pedagogical AI planner & Gemini integration
│   │   ├── tts_engine.py        # Neural TTS, duration calculation & WebVTT generator
│   │   ├── visual_engine.py     # Pillow HD frame renderer & FFmpeg video compositor
│   │   └── storage_service.py   # JSON lecture persistence & scene updates
│   ├── static/
│   │   ├── css/style.css        # Modern dark glassmorphic design system
│   │   └── js/
│   │       ├── app.js           # Client orchestration, quiz, flashcards, player controls
│   │       └── visual_renderer.js # 60FPS HTML5 Canvas dynamic visual engine
│   ├── templates/
│   │   └── index.html           # Single-page educational studio layout
│   └── media/                   # Generated audio, videos, and subtitles
├── data/
│   └── lectures.json            # Persistent lecture database
├── run.py                       # Easy launch script
└── README.md                    # Project documentation
```
