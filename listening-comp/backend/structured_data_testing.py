from typing import Optional, Dict, List
import requests
import json
import traceback
import os

# Model ID
#MODEL_ID = "amazon.nova-micro-v1:0"
#MODEL_ID = "llama3.2:1b"

class TranscriptStructurer:
    def __init__(self):
        #self.MODEL_ID = "llama3.2:1b"
        self.MODEL_ID = "deepseek-r1"
        self.ollama_url = 'http://localhost:9000/api/chat'  # URL for the local Ollama service
        self.prompts = {
            1: """ Why is the sky blue?\n""",
            2: """ At what temperature does water boil?\n""",
            3: """ Are dogs or cats a better pet?\n"""}

    def _invoke_ollama(self, prompt: str, transcript: str) -> Optional[str]:
        print("Start of invoke_ollama")
        full_prompt = f"{prompt}\n\nHere's the transcript:\n{transcript}"
        print("full_prompt length: ", str(len(full_prompt)))
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(self.ollama_url, json={'prompt': full_prompt, 'model': self.MODEL_ID}, headers=headers)
            print("Response content: ", response.content)
            #response = requests.post(self.ollama_url, json={'prompt': full_prompt}, headers=headers)
            print("response from requests.post: ", str(response.status_code))
            if response.status_code != 200:
                print(f"Error: {response.status_code}, Message: {response.text}")
                return None
            print("Response output: ", str(response.json().get('output')))
            return response.json().get('output')
        except Exception as e:
            print(f"Error invoking Ollama: {str(e)}")
            traceback.print_exc()
            return None

    def structure_transcript(self, transcript: str) -> Dict[int, str]:
        results = {}
        print("Structure_transcript start.")
        for section_num in range(1, 4):  # Adjusted to include section 1
            print("section_num: ", str(section_num))
            result = self._invoke_ollama(self.prompts[section_num], transcript)
            print("Result: ", str(result))
            if result:
                results[section_num] = result
        return results

    def save_questions(self, structured_sections: Dict[int, str], base_filename: str) -> bool:
        """Save each section to a separate file"""
        try:
            # Create questions directory if it doesn't exist
            os.makedirs(os.path.dirname(base_filename), exist_ok=True)
            
            # Save each section
            for section_num, content in structured_sections.items():
                filename = f"{os.path.splitext(base_filename)[0]}_section{section_num}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            return True
        except Exception as e:
            print(f"Error saving questions: {str(e)}")
            return False

    def load_transcript(self, filename: str) -> Optional[str]:
        """Load transcript from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading transcript: {str(e)}")
            return None

if __name__ == "__main__":
    MODEL_ID = "deepseek-r1"
    ollama_url = 'http://localhost:9000/api/chat'  # URL for the local Ollama service
    headers = {'Content-Type': 'application/json'}
 
    print("url:", ollama_url)
    print("MODEL_ID: ", MODEL_ID)
    simple_prompt = "Why is the sky blue?"
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "user", "content": simple_prompt}
        ]
    }
    response = requests.post(ollama_url, json=payload, headers=headers)
    #response = requests.post(ollama_url, json={'prompt': simple_prompt, 'model': MODEL_ID}, headers=headers)
    print("Response content: ", response.content)

"""
    structurer = TranscriptStructurer()
    transcript = structurer.load_transcript("transcripts/sY7L5cfCWno.txt")
    if transcript:
        #print("Transcript loaded:", transcript)  # Debug print
        structured_sections = structurer.structure_transcript(transcript)
        print("Structured sections:", structured_sections)  # Debug print
        structurer.save_questions(structured_sections, "questions/sY7L5cfCWno.txt")
        print("Questions saved successfully")
        """