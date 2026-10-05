from multimodel import process_pos_input

print("Sending text request to Ollama (this might take a few seconds)...")

try:
    # Test with a simple text command
    response = process_pos_input(text="add 3 kilo potatoes and remove 1 kg apples")
    
    print("\n--- RESPONSE FROM Gemini ---")
    print(response)
    print("----------------------------\n")
    
except Exception as e:
    print(f"\nOops! Something went wrong connecting to Gemini:\n{e}")
