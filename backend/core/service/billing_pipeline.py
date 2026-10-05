import os
import sys
import tempfile
import json
from pydub import AudioSegment
from .verification import verify_billing_action

# Add the parent directory of backend to sys.path so we can import llm_point
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(BASE_DIR)

from llm_point.voice import transcribe_audio_file
from llm_point.multimodel import process_pos_input

def convert_to_wav(input_path: str, output_path: str):
    """Converts an audio file to .wav format using pydub."""
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")

def process_voice_billing(audio_file_path: str):
    """Processes a voice input: converts to wav, transcribes, gets LLM JSON, and verifies it."""
    ext = os.path.splitext(audio_file_path)[1].lower()
    if ext != ".wav":
        wav_path = tempfile.mktemp(suffix=".wav")
        convert_to_wav(audio_file_path, wav_path)
    else:
        wav_path = audio_file_path

    try:
        # Transcribe voice
        transcription = transcribe_audio_file(wav_path)
        
        # Process with LLM
        llm_response = process_pos_input(text=transcription)
        
        # Verify output
        return verify_billing_action(llm_response)
    finally:
        # Cleanup temporary wav file if we created one
        if ext != ".wav" and os.path.exists(wav_path):
            os.remove(wav_path)

def process_text_billing(text: str):
    """Processes text input."""
    llm_response = process_pos_input(text=text)
    return verify_billing_action(llm_response)

def process_image_billing(image_b64: str, mime_type: str = "image/jpeg", text: str = None):
    """Processes image input (optionally with text)."""
    llm_response = process_pos_input(text=text, image_b64=image_b64, image_mime_type=mime_type)
    return verify_billing_action(llm_response)
