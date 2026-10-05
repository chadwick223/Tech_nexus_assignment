# AI-Powered POS System

A modern, multi-modal Point-of-Sale (POS) system built with Django. This system allows cashiers and customers to add items to a cart via text, voice, or image uploads, while also providing a complete manual fallback interface. 

It leverages advanced Large Language Models (LLMs) and Vision Models to parse natural language, speech, and images into structured cart data, seamlessly verified against a live local inventory.

## Features

- **Multi-Modal AI Inputs:**
  - **Voice:** Speak commands (e.g., *"Add two liters of milk and a loaf of bread"*). Uses `pydub` and AI to extract items.
  - **Text:** Type natural language commands into the interface.
  - **Vision/Images:** Upload a picture of products or a receipt, and the Vision pipeline will identify the items.
- **Robust AI Processing Pipeline:**
  - Connects to Google Gemini and Sarvam AI APIs.
  - Features internal normalization to map colloquial terms or different languages (e.g., "ek kilo aaloo") to structured catalog IDs ("potato").
- **Live POS Interface:**
  - A clean, dark-mode responsive UI built with vanilla HTML/CSS (Flexbox) and JavaScript.
  - Live, auto-updating order summary reflecting quantities, line totals, and grand total.
- **Manual Overrides:**
  - Increase/decrease item quantities and delete items with a single click.
  - A manual addition section dynamically tied to the live inventory.
- **Lightweight JSON Database:**
  - Requires no complex SQL setup. State is stored natively in `backend/data/cart.json` and `backend/data/inventory.json`.
  - Implements atomic `filelock` safety to prevent concurrent write collisions between AI updates and manual cashier updates.

## Tech Stack

- **Backend:** Python, Django
- **Frontend:** Vanilla HTML, CSS (Flexbox), JavaScript
- **AI / Integrations:** Google GenAI (Gemini), Sarvam AI, `pydub` (for audio processing)
- **Data Layer:** Local JSON files with atomic locking (`filelock`)

## Setup Instructions

### Prerequisites
- Python 3.11+
- [FFmpeg](https://ffmpeg.org/) installed and added to your system PATH (required for processing voice audio files).

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
Create a `.env` file in the root directory (or in your deployment environment) and add your API keys:
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

## Deployment Note
Because this application uses a lightweight local JSON database (`cart.json`) and requires `ffmpeg` for audio conversions, it **cannot** be deployed to Serverless platforms with read-only filesystems (like Vercel or AWS Lambda). 

It is designed to be run on a traditional Virtual Machine (VM) such as an AWS EC2 instance, DigitalOcean Droplet, Railway, or Render (as a background web service).
