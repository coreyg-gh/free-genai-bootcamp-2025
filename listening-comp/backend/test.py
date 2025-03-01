import requests
import json

MODEL_ID = "deepseek-r1"
ollama_url = 'http://localhost:9000/api/chat'  # URL for the local Ollama service
headers = {'Content-Type': 'application/json'}

print("url:", ollama_url)
print("MODEL_ID: ", MODEL_ID)
prompt_content = "Why is the sky blue?"

for model in [MODEL_ID, "llama3.2:1b"]:
    print(f"testing model: {model}")
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt_content}
        ]
    }
    response = requests.post(ollama_url, json=payload, headers=headers)

    print(f"Status Code: {response.status_code}")

    try:
        response_json = response.json()
        print(f"Response content: {response_json}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON: {response.content}")