import streamlit as st
import json
import requests
from typing import List, Dict, Optional
from duckduckgo_search import DDGS
from html2text import HTML2Text
import time
import re

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
        
        # Define language-specific formatting rules
        language_formats = {
            "Japanese": """
                Rules for Japanese:
                1. Use kanji with common readings
                2. NO romaji or English characters
                3. NO numbers or special characters
                4. Example format:
                   book: 本
                   study: 勉強
                   read: 読む
            """,
            "Chinese": """
                Rules for Chinese:
                1. Use simplified Chinese characters
                2. NO pinyin or English
                3. Example format:
                   book: 书
                   study: 学习
                   read: 读
            """,
            "Spanish": """
                Rules for Spanish:
                1. Use proper Spanish accents
                2. NO explanations
                3. Example format:
                   book: libro
                   study: estudiar
                   read: leer
            """,
            "French": """
                Rules for French:
                1. Use proper French accents
                2. NO explanations
                3. Example format:
                   book: livre
                   study: étudier
                   read: lire
            """,
            "German": """
                Rules for German:
                1. Use proper German umlauts
                2. NO explanations
                3. Example format:
                   book: Buch
                   study: studieren
                   read: lesen
            """,
            "Italian": """
                Rules for Italian:
                1. Use proper Italian accents
                2. NO explanations
                3. Example format:
                   book: libro
                   study: studiare
                   read: leggere
            """
        }
        
        # Get language-specific format or use default
        language_specific_format = language_formats.get(target_language, "")
        
        for i in range(0, len(words), batch_size):
            batch = words[i:i + batch_size]
            
            # Create a more strict and clear prompt
            if target_language == "Japanese":
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a Japanese translator. Translate each English word to Japanese.\n"
                            "STRICT RULES:\n"
                            "1. Use ONLY this format: english: 日本語\n"
                            "2. One word per line\n"
                            "3. Always provide a translation\n"
                            "4. Use common, basic translations\n"
                            "5. NO parentheses or explanations\n"
                            "Example correct format:\n"
                            "hello: こんにちは\n"
                            "world: 世界\n"
                            "book: 本\n"
                            "a: ひとつの\n"
                            "the: その\n"
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            "Translate these words to Japanese:\n" +
                            "\n".join(batch)
                        )
                    }
                ]
            else:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            f"You are a professional {target_language} translator.\n"
                            "RULES:\n"
                            "1. ONLY use format 'word: translation'\n"
                            "2. One translation per line\n"
                            "3. NO explanations or notes\n"
                            "4. NO English unless it's the same word in target language\n"
                            f"{language_specific_format}\n"
                        )
                    },
                    {
                        "role": "user",
                        "content": "\n".join(batch)
                    }
                ]
            
            try:
                print(f"\nTranslating batch: {batch}")
                translation_result = self._try_translation(batch, messages, target_language)
                
                # If any translations failed, try one more time
                failed_words = [pair["original"] for pair in translation_result 
                              if pair["translation"].startswith("[")]
                
                if failed_words:
                    print(f"\nRetrying failed words: {failed_words}")
                    retry_messages = [
                        {
                            "role": "system",
                            "content": (
                                f"Translate these specific words to {target_language} only.\n"
                                "Format: word: translation\n"
                                f"{language_specific_format}\n"
                            )
                        },
                        {
                            "role": "user",
                            "content": "\n".join(failed_words)
                        }
                    ]
                    
                    retry_results = self._try_translation(failed_words, retry_messages, target_language)
                    
                    # Update original results with successful retries
                    for retry_pair in retry_results:
                        if not retry_pair["translation"].startswith("["):
                            for pair in translation_result:
                                if pair["original"] == retry_pair["original"]:
                                    pair["translation"] = retry_pair["translation"]
                                    break
                
                translated_pairs.extend(translation_result)
                
            except Exception as e:
                print(f"Translation batch failed: {str(e)}")
                for word in batch:
                    translated_pairs.append({
                        "original": word,
                        "translation": f"[Translation failed: {str(e)}]"
                    })
        
        time.sleep(0.5)  # Small delay between batches
        
        # Separate successful and failed translations
        successful = [pair for pair in translated_pairs 
                     if not pair["translation"].startswith("[")]
        failed = [{"word": pair["original"], 
                   "reason": pair["translation"][1:-1]}  # Remove brackets
                  for pair in translated_pairs 
                  if pair["translation"].startswith("[")]
        
        return successful, failed

    def _try_translation(self, words: List[str], messages: List[Dict[str, str]], target_language: str) -> List[Dict[str, str]]:
        """Helper method to attempt translation with detailed debugging."""
        result = []
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "temperature": 0.1  # Reduced temperature for more consistent output
            }
            
            response = requests.post(self.ollama_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            
            if 'message' in response_data:
                translation_text = response_data['message']['content'].strip()
                print(f"Raw translation response:\n{translation_text}")
                
                # Split into lines and clean up
                lines = [line.strip() for line in translation_text.split('\n') 
                        if line.strip() and ':' in line]
                
                # Create a dictionary of translations
                translations_dict = {}
                for line in lines:
                    # Skip lines that don't match our expected format
                    if not re.match(r'^[a-zA-Z]+:', line):
                        continue
                        
                    parts = line.split(':', 1)
                    if len(parts) != 2:
                        continue
                        
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    
                    # For Japanese, validate characters
                    if target_language == "Japanese":
                        value = ''.join(char for char in value 
                                      if ('\u3040' <= char <= '\u309f' or  # Hiragana
                                          '\u30a0' <= char <= '\u30ff' or  # Katakana
                                          '\u4e00' <= char <= '\u9fff'))   # Kanji
                        
                        # Skip empty or invalid translations
                        if not value or len(value) < 1:
                            continue
                            
                        # Skip if it looks like romaji or contains numbers
                        if re.search(r'[a-zA-Z0-9]', value):
                            continue
                    
                    translations_dict[key] = value
                
                # Process each word
                for word in words:
                    word_lower = word.lower()
                    
                    if word_lower in translations_dict:
                        result.append({
                            "original": word,
                            "translation": translations_dict[word_lower]
                        })
                        print(f"Found translation for '{word}': '{translations_dict[word_lower]}'")
                    else:
                        print(f"No translation found for '{word}'")
                        result.append({
                            "original": word,
                            "translation": "[Missing translation]"
                        })
            
            else:
                print("No message in response data")
                for word in words:
                    result.append({
                        "original": word,
                        "translation": "[No response]"
                    })
        
        except Exception as e:
            print(f"Translation request failed: {str(e)}")
            for word in words:
                result.append({
                    "original": word,
                    "translation": "[Request failed]"
                })
        
        return result

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
                                            successful_translations, failed_translations = agent.translate_words(sample_words, target_language)
                                            
                                            if successful_translations:
                                                st.subheader("Successful Translations")
                                                st.table({
                                                    "Original": [pair["original"] for pair in successful_translations],
                                                    f"{target_language}": [pair["translation"] for pair in successful_translations]
                                                })
                                            
                                            if failed_translations:
                                                st.subheader("Failed Translations")
                                                st.table({
                                                    "Word": [pair["word"] for pair in failed_translations],
                                                    "Reason": [pair["reason"] for pair in failed_translations]
                                                })
                                                
                                                st.warning(f"Failed to translate {len(failed_translations)} words. See details above.")
                                            
                                            if not successful_translations and not failed_translations:
                                                st.error("Translation failed. Please check if Ollama is running and try again.")
                                                st.code("Run Ollama with: ollama run llama2")
                                    
                                    with col2:
                                        if st.button("Show All Vocabulary"):
                                            with st.spinner("Translating all words..."):
                                                translations, failed_translations = agent.translate_words(sorted(vocabulary), target_language)
                                                st.table({
                                                    "Original": [pair["original"] for pair in translations],
                                                    f"{target_language}": [pair["translation"] for pair in translations]
                                                })
        else:
            st.error("No results found for this song. Try another search.")

    # Footer
    st.markdown("---")
    st.markdown("Made with lots of help from AI!")
if __name__ == "__main__":
    main()














