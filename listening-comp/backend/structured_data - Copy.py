from typing import Optional, Dict, List
import requests
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
            1: """Extract questions from section 1 of this JLPT transcript where the answer can be determined solely from the conversation without needing visual aids.
            
            ONLY include questions that meet these criteria:
            - The answer can be determined purely from the spoken dialogue
            - No spatial/visual information is needed (like locations, layouts, or physical appearances)
            - No physical objects or visual choices need to be compared
            
            For example, INCLUDE questions about:
            - Times and dates
            - Numbers and quantities
            - Spoken choices or decisions
            - Clear verbal directions
            
            DO NOT include questions about:
            - Physical locations that need a map or diagram
            - Visual choices between objects
            - Spatial arrangements or layouts
            - Physical appearances of people or things

            Format each question exactly like this:

            <question>
            Introduction:
            [the situation setup in japanese]
            
            Conversation:
            [the dialogue in japanese]
            
            Question:
            [the question being asked in japanese]

            Options:
            1. [first option in japanese]
            2. [second option in japanese]
            3. [third option in japanese]
            4. [fourth option in japanese]
            </question>

            Rules:
            - Only extract questions from the 1 section
            - Only include questions where answers can be determined from dialogue alone
            - Ignore any practice examples (marked with 例)
            - Do not translate any Japanese text
            - Do not include any section descriptions or other text
            - Output questions one after another with no extra text between them
            """,
            
            2: """Extract questions from section 2 of this JLPT transcript where the answer can be determined solely from the conversation without needing visual aids.
            
            ONLY include questions that meet these criteria:
            - The answer can be determined purely from the spoken dialogue
            - No spatial/visual information is needed (like locations, layouts, or physical appearances)
            - No physical objects or visual choices need to be compared
            
            For example, INCLUDE questions about:
            - Times and dates
            - Numbers and quantities
            - Spoken choices or decisions
            - Clear verbal directions
            
            DO NOT include questions about:
            - Physical locations that need a map or diagram
            - Visual choices between objects
            - Spatial arrangements or layouts
            - Physical appearances of people or things

            Format each question exactly like this:

            <question>
            Introduction:
            [the situation setup in japanese]
            
            Conversation:
            [the dialogue in japanese]
            
            Question:
            [the question being asked in japanese]
            </question>

            Rules:
            - Only extract questions from the 2 section
            - Only include questions where answers can be determined from dialogue alone
            - Ignore any practice examples (marked with 例)
            - Do not translate any Japanese text
            - Do not include any section descriptions or other text
            - Output questions one after another with no extra text between them
            """,
            
            3: """Extract all questions from section 3 of this JLPT transcript.
            Format each question exactly like this:

            <question>
            Situation:
            [the situation in japanese where a phrase is needed]
            
            Question:
            何と言いますか
            </question>

            Rules:
            - Only extract questions from the 3 section
            - Ignore any practice examples (marked with 例)
            - Do not translate any Japanese text
            - Do not include any section descriptions or other text
            - Output questions one after another with no extra text between them
            """
        }

    def _invoke_ollama(self, prompt: str, transcript: str) -> Optional[str]:
        print("Start of invoke_ollama")
        full_prompt = f"{prompt}\n\nHere's the transcript:\n{transcript}"
        print("full_prompt length: ", str(len(full_prompt)))
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(self.ollama_url, json={'prompt': full_prompt, 'model': self.MODEL_ID}, headers=headers)
            #response = requests.post(self.ollama_url, json={'prompt': full_prompt}, headers=headers)
            print("response from requests.post: ", str(response.status_code))
            if response.status_code != 200:
                print(f"Error: {response.status_code}, Message: {response.text}")
                return None
            print("Response output: ", str(response.json().get('output')))
            return response.json().get('output')
        except Exception as e:
            print(f"Error invoking Ollama: {str(e)}")
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
    structurer = TranscriptStructurer()
    transcript = structurer.load_transcript("transcripts/sY7L5cfCWno.txt")
    if transcript:
        #print("Transcript loaded:", transcript)  # Debug print
        structured_sections = structurer.structure_transcript(transcript)
        print("Structured sections:", structured_sections)  # Debug print
        structurer.save_questions(structured_sections, "questions/sY7L5cfCWno.txt")
        print("Questions saved successfully")