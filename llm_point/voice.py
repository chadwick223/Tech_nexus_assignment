import os
from sarvamai import SarvamAI
from dotenv import load_dotenv

# Safely load the .env file located in the same directory as this file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

def transcribe_audio_file(file_path: str) -> str:
    """
    Takes a path to an audio file (e.g. .wav) and uses Sarvam AI to transcribe it.
    """
    # Initialize the Sarvam client using the API key from .env
    api_key = os.getenv("SARVAM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("SARVAM_API_KEY environment variable is not set!")

    client = SarvamAI(api_subscription_key=api_key)

    with open(file_path, "rb") as f:
        # Hit the Sarvam speech-to-text API
        response = client.speech_to_text.transcribe(
            file=f,
            model="saaras:v4",
            language_code="en-IN",
            mode="transcribe",
        )

    # Return the transcribed text
    
    return response.transcript

if __name__ == "__main__":
    print(transcribe_audio_file(r"C:\Users\satvi\OneDrive\Desktop\Project\llm_point\voice_test.wav"))