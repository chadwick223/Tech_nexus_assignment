import requests
import sys
import os

API_URL = "http://127.0.0.1:8000/cart/process/command/"

def test_vision(image_path: str):
    if not os.path.exists(image_path):
        print(f"Error: Could not find image at {image_path}")
        return
        
    print(f"Uploading {image_path} to {API_URL}...")
    
    # Determine basic mime type for logging
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = 'image/png' if ext == '.png' else 'image/jpeg'
    if ext == '.webp':
        mime_type = 'image/webp'
        
    print(f"Detected MIME type: {mime_type}")
    
    # Send as multipart/form-data
    with open(image_path, 'rb') as f:
        files = {
            'image': (os.path.basename(image_path), f, mime_type)
        }
        
        response = requests.post(API_URL, files=files)
        
        if response.status_code == 200:
            print("\nSuccess! Here is the updated cart:")
            print(response.json())
        else:
            print(f"\nFailed! Status Code: {response.status_code}")
            try:
                print(response.json())
            except:
                print(response.text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_vision.py <path_to_image>")
        print("Example: python test_vision.py apple.jpg")
    else:
        test_vision(sys.argv[1])
