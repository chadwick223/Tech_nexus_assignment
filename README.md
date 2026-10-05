# AI-Powered POS System

A modern, multi-modal Point-of-Sale (POS) system built with Django. This system allows cashiers and customers to add items to a cart via text, voice, or image uploads, while also providing a complete manual fallback interface. 

It leverages advanced Large Language Models (LLMs) and Vision Models to parse natural language, speech, and images into structured cart data, seamlessly verified against a live local inventory.

## Features

- **Multi-Modal AI Inputs:**
  - **Voice (Continuous Loop):** Speak commands (e.g., *"Add two liters of milk and a loaf of bread"*). Features an automatic silence-detection loop that processes audio completely hands-free!
  - **Text:** Type natural language commands into the interface.
  - **Vision/Images:** Snap a photo using the **Live Camera** directly in the browser, or upload a receipt to identify items automatically!
- **Robust AI Processing Pipeline:**
  - Connects to Google Gemini and Sarvam AI APIs.
  - Internal normalization maps colloquial terms (e.g., "ek kilo aaloo") to structured catalog IDs ("potato").
- **Live POS Interface:**
  - A clean, dark-mode responsive UI built with vanilla HTML/CSS and JavaScript.
  - Live, auto-updating order summary reflecting quantities, line totals, and grand total.
- **Manual Overrides:**
  - Increase/decrease item quantities and delete items with a single click.
  - A manual addition section dynamically tied to the live inventory.
- **Lightweight JSON Database:**
  - State is stored natively in `backend/data/cart.json` and `backend/data/inventory.json` using atomic `filelock` safety to prevent concurrent write collisions.

## Tech Stack

- **Backend:** Python, Django
- **Frontend:** Vanilla HTML, CSS, JavaScript (Static files served by WhiteNoise)
- **AI / Integrations:** Google GenAI (Gemini), Sarvam AI
- **Audio Processing:** `imageio-ffmpeg` (Bundled FFmpeg binary for cross-platform zero-dependency deployment).
- **Data Layer:** Local JSON files with atomic locking (`filelock`)

## Setup Instructions

### Prerequisites
- Python 3.11+
- No system-level dependencies required! FFmpeg is now automatically bundled.

### 1. Clone & Environment
```bash
git clone https://github.com/chadwick223/Tech_nexus_assignment.git
cd Tech_nexus_assignment
python -m venv .venv
# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory (or in your deployment dashboard) and add your API keys:
```env
GEMINI_API_KEY="your_gemini_key_here"
SARVAM_API_KEY="your_sarvam_key_here"
```

### 4. Run the Server
```bash
cd backend
python manage.py runserver
```

Navigate to `http://127.0.0.1:8000/` in your browser to access the POS Interface!

## Deployment Notes
This application is perfectly configured for production deployment on Platforms-as-a-Service (PaaS) like **Render.com**.
- **Static Files:** Served via WhiteNoise. Ensure your build command includes `python manage.py collectstatic --noinput`.
- **Audio Processing:** Completely platform agnostic. By utilizing `imageio-ffmpeg`, the FFmpeg binary is bundled securely in the Python environment without requiring root `apt-get` packages.
- **Data Storage:** Uses JSON file storage. On ephemeral cloud hosting like Render's free tier, this data will reset upon a new deployment. For persistent data, attach a Render Disk to the `/data` directory.
