import os
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Safely load the .env file located in the same directory as this file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Safely get the Gemini API key from the environment
api_key = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = """You are the central intelligence engine for a Point-of-Sale (POS) billing system. Your sole purpose is to convert unstructured inputs (text commands, transcribed Hinglish/Hindi voice commands, and images of products/receipts) into a strict, validated JSON object.
You will receive either:
1. A text command (e.g., "add 2 kilo potatoes", "remove dhai kg apples").
2. An image (a camera scan of products or a receipt).
3. Both text and an image (e.g., Image of a receipt + "add these items").

RULES FOR EXTRACTION:
- Actions: Determine the core intent. Permitted values are "add", "remove", "set", "clear". If processing an image without a specific text command, default to "add".
- Item Normalization: ALWAYS convert item names to their singular, lowercase form (e.g., "apples" -> "apple", "potatoes" -> "potato", "bread loaves" -> "bread_loaf").
- Number Normalization: Convert all regional Hindi/Hinglish spoken numbers to exact floating-point values. (e.g., "ek" = 1.0, "do" = 2.0, "aadha" = 0.5, "dhai" = 2.5, "dedh" = 1.5).
- Unit Standardization: Convert to base metrics where logical (e.g., "500g" = 0.5, "100ml" = 0.1).
- Image Processing: If an image is provided, extract visible products and their quantities. Ignore background noise.

OUTPUT FORMAT:
You must output ONLY valid JSON. Do not include markdown formatting, backticks, or conversational text. Use this exact schema:
{
  "action": "add | remove | set | clear",
  "items": [
    {
      "item_name": "string (product name)",
      "quantity": float (normalized numeric value),
      "unit": "string (optional, standard unit)"
    }
  ]
}"""

def process_pos_input(text=None, image_b64=None, image_mime_type='image/jpeg'):
    if not text and not image_b64:
        raise ValueError("Must provide either text or an image.")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set in your .env file!")

    # Initialize the Google Gemini client
    client = genai.Client(api_key=api_key)

    # Build the contents array (Gemini accepts text and raw image bytes mixed together in a list)
    contents = []

    if image_b64:
        # Convert base64 string back to raw bytes for Gemini
        image_bytes = base64.b64decode(image_b64)
        contents.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=image_mime_type,
            )
        )

    if text:
        contents.append(text)
    else:
        contents.append("Extract the items from this image according to the system instructions.")

    # Call Gemini Flash (the fast, free, multi-modal model)
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.0, # Keep it strictly deterministic
            response_mime_type="application/json", # This physically forces the model to return ONLY valid JSON!
        ),
    )

    return response.text