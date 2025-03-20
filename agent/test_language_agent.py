import requests
import json

def test_ollama_connection():
    MODEL_ID = "llama3.2:1b"
    ollama_url = 'http://localhost:9000/api/chat'
    headers = {'Content-Type': 'application/json'}
    
    print(f"Testing connection to Ollama at {ollama_url}")
    
    test_payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "user", "content": "Say hello in Japanese"}
        ]
    }
    
    try:
        response = requests.post(ollama_url, json=test_payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Handle streaming response
        outputs = []
        for line in response.content.splitlines():
            if line.strip():  # Skip empty lines
                try:
                    response_data = json.loads(line)
                    if 'message' in response_data:
                        outputs.append(response_data['message'].get('content', ''))
                except json.JSONDecodeError as e:
                    print(f"Error decoding line: {line.decode('utf-8')}")
                    continue
        
        combined_response = ''.join(outputs)
        print(f"Response: {combined_response}")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_ollama_connection()
