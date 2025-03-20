import streamlit as st
import json
import requests
from typing import List, Dict, Optional
from duckduckgo_search import DDGS
from html2text import HTML2Text
import time

class LanguageAgent:
    def __init__(self, host: str = "localhost", port: int = 9000):
        self.ollama_url = f"http://{host}:{port}/api/chat"  # Changed back to /api/chat
        self.headers = {'Content-Type': 'application/json'}
        # self.model = "deepseek-r1"
        self.model = "llama3.2:1b"
        
    def search_web(self, query: str) -> List[Dict]:
        """Search the web for information."""
        results = DDGS().text(query, max_results=10)
        if results:
            return [
                {
                    "title": result["title"],
                    "url": result["href"],
                }
                for result in results
            ]
        return []

    def get_page_content(self, url: str) -> str:
        """Get the content of a web page."""
        try:
            # Add headers to make request look more like a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            h = HTML2Text()
            h.ignore_links = False
            content = h.handle(response.text)
            return content[:4000] if len(content) > 4000 else content
        
        except requests.exceptions.RequestException as e:
            print(f"\nError accessing URL {url}: {str(e)}")
            print("Skipping this result and continuing with the next one...")
            return ""

    def extract_vocabulary(self, text: str) -> List[str]:
        """Extract vocabulary from text."""
        words = set(text.lower().split())
        vocabulary = [word for word in words if word.isalpha()]
        return sorted(vocabulary)

    def translate_words(self, words: List[str], target_language: str) -> List[Dict[str, str]]:
        """Translate a list of words to the target language."""
        translated_pairs = []
        batch_size = 5  # Process 5 words at a time
        
        for i in range(0, len(words), batch_size):
            batch = words[i:i + batch_size]
            
            # Format messages for chat API
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are a translator. Translate each of these words to {target_language}.\n"
                        "IMPORTANT: You must provide exactly one translation per word, one per line.\n"
                        "Format: word: translation"
                    )
                },
                {
                    "role": "user",
                    "content": "\n".join(batch)
                }
            ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "temperature": 0.3
            }
            
            try:
                print(f"\nTranslating batch: {batch}")
                response = requests.post(self.ollama_url, json=payload, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                response_data = response.json()
                
                if 'message' in response_data:
                    translation_text = response_data['message']['content'].strip()
                    print(f"Raw translation response:\n{translation_text}")
                    
                    # Process each line of the response
                    lines = [line.strip() for line in translation_text.split('\n') if line.strip()]
                    
                    # Ensure we have a translation for each word in the batch
                    for word_idx, word in enumerate(batch):
                        try:
                            # Try to find a line that contains this word
                            matching_line = None
                            for line in lines:
                                if word.lower() in line.lower():
                                    matching_line = line
                                    break
                            
                            if matching_line and ':' in matching_line:
                                _, translation = matching_line.split(':', 1)
                                translation = translation.strip()
                            elif word_idx < len(lines):
                                # Fallback: use the line at the same index
                                line = lines[word_idx]
                                if ':' in line:
                                    _, translation = line.split(':', 1)
                                    translation = translation.strip()
                                else:
                                    translation = line.strip()
                            else:
                                translation = "[Missing translation]"
                            
                            # Validate translation
                            if translation and not any(invalid in translation.lower() for invalid in ['<', 'let', '[', 'translation']):
                                translated_pairs.append({
                                    "original": word,
                                    "translation": translation
                                })
                            else:
                                print(f"Invalid translation for '{word}': {translation}")
                                translated_pairs.append({
                                    "original": word,
                                    "translation": "[Invalid translation]"
                                })
                                
                        except Exception as e:
                            print(f"Error processing translation for '{word}': {str(e)}")
                            translated_pairs.append({
                                "original": word,
                                "translation": "[Error]"
                            })
                else:
                    print("No message in response data")
                    for word in batch:
                        translated_pairs.append({
                            "original": word,
                            "translation": "[No response]"
                        })
            
            except Exception as e:
                print(f"Translation batch failed: {str(e)}")
                for word in batch:
                    translated_pairs.append({
                        "original": word,
                        "translation": "[Translation failed]"
                    })
            
            time.sleep(0.5)  # Small delay between batches
        
        # Verify we have translations for all words
        if len(translated_pairs) != len(words):
            print(f"Warning: Translation count mismatch. Expected {len(words)}, got {len(translated_pairs)}")
            # Add missing translations
            translated_words = {pair["original"] for pair in translated_pairs}
            for word in words:
                if word not in translated_words:
                    print(f"Adding missing translation for: {word}")
                    translated_pairs.append({
                        "original": word,
                        "translation": "[Missing translation]"
                    })
        
        return translated_pairs

    def chat_completion(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Improved chat completion with better error handling and debugging"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": 0.3
        }
        
        try:
            print(f"Sending request to Ollama: {json.dumps(payload, indent=2)}")
            response = requests.post(self.ollama_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)}")
            
            if 'message' in response_data:
                return response_data['message']['content'].strip()
            
            print("Warning: Empty or invalid response received")
            return None
            
        except Exception as e:
            print(f"Error in chat completion: {str(e)}")
            return None

def main():
    st.set_page_config(
        page_title="Language Learning Song Assistant",
        page_icon="🎵",
        layout="wide"
    )

    st.title("🎵 Language Learning Song Assistant")
    st.markdown("---")

    # Initialize the agent
    agent = LanguageAgent()

    # Sidebar for language selection
    with st.sidebar:
        st.header("Settings")
        target_language = st.selectbox(
            "Select target language",
            ["Spanish", "French", "German", "Japanese", "Italian", "Chinese"],
            index=0
        )
        
        st.markdown("### How to use")
        st.markdown("""
        1. Enter a song title
        2. Select search results to analyze
        3. View vocabulary and translations
        """)

    # Main content area
    song_title = st.text_input("Enter a song title to search for:", placeholder="Enter song title here...")

    if song_title:
        with st.spinner(f"Searching for information about: {song_title}"):
            search_results = agent.search_web(f"{song_title} song information lyrics meaning")

        if search_results:
            st.subheader("Found relevant information")
            
            for i, result in enumerate(search_results[:3], 1):
                with st.expander(f"Result {i}: {result['title']}", expanded=True):
                    st.write(f"Source: {result['url']}")
                    
                    if st.button(f"Analyze Result {i}", key=f"analyze_{i}"):
                        with st.spinner("Fetching and analyzing content..."):
                            content = agent.get_page_content(result['url'])
                            
                            if not content:
                                st.error("Could not retrieve content from this source.")
                            else:
                                vocabulary = agent.extract_vocabulary(content)
                                if not vocabulary:
                                    st.warning("No processable text found in this content.")
                                else:
                                    st.success(f"Found {len(vocabulary)} unique words!")
                                    
                                    # Create two columns for vocabulary display
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.subheader("Sample Vocabulary")
                                        sample_words = sorted(vocabulary)[:10]
                                        
                                        with st.spinner("Translating sample words..."):
                                            translations = agent.translate_words(sample_words, target_language)
                                            
                                            # Filter out failed translations
                                            valid_translations = [t for t in translations if not t["translation"].startswith("[")]
                                            failed_translations = [t for t in translations if t["translation"].startswith("[")]
                                            
                                            if failed_translations:
                                                st.warning(f"Failed to translate {len(failed_translations)} words. Showing successful translations only.")
                                            
                                            if valid_translations:
                                                st.table({
                                                    "Original": [pair["original"] for pair in valid_translations],
                                                    f"{target_language}": [pair["translation"] for pair in valid_translations]
                                                })
                                            else:
                                                st.error("Translation failed. Please check if Ollama is running and try again.")
                                                st.code("Run Ollama with: ollama run llama2")
                                    
                                    with col2:
                                        if st.button("Show All Vocabulary"):
                                            with st.spinner("Translating all words..."):
                                                translations = agent.translate_words(sorted(vocabulary), target_language)
                                                st.table({
                                                    "Original": [pair["original"] for pair in translations],
                                                    f"{target_language}": [pair["translation"] for pair in translations]
                                                })
        else:
            st.error("No results found for this song. Try another search.")

    # Footer
    st.markdown("---")
    # st.markdown("Made with ❤️ by Language Learning Song Assistant")
    st.markdown("Made with lots of help from AI!")
if __name__ == "__main__":
    main()






