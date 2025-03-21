import streamlit as st
import json
import requests
from typing import List, Dict, Optional
from duckduckgo_search import DDGS
from html2text import HTML2Text
import time
import re
from collections import Counter

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
                4. Example format that you must return:
                   book: 本
                   study: 勉強
                   read: 読む
                5. Do not provide any explanations, only return the Engligh and translated Japanese words.
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
                            "CRITICAL RULES:\n"
                            "1. MUST use format 'english: japanese'\n"
                            "2. One translation per line\n"
                            "3. Use ONLY kanji, hiragana, or katakana\n"
                            "4. NO romaji, NO English, NO explanations\n"
                            "5. For articles (a, an, the) use これ, その, あの\n"
                            "6. Common translations only\n"
                            "Example format:\n"
                            "book: 本\n"
                            "study: 勉強\n"
                            "read: 読む\n"
                            "a: これ\n"
                            "the: その\n"
                            "and: そして\n"
                            "all: 全て\n"
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            "Translate these words to Japanese (format 'english: japanese'):\n" +
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
                            "STRICT FORMAT RULES:\n"
                            "1. MUST use format 'english_word: translation'\n"
                            "2. English word MUST be on the left side of the colon\n"
                            "3. Translation MUST be on the right side of the colon\n"
                            "4. One translation per line\n"
                            "5. NO explanations or notes\n"
                            "6. NO English unless it's the same word in target language\n"
                            "7. ALWAYS provide a translation for every word\n"
                            f"{language_specific_format}\n"
                            "Example correct format:\n"
                            "book: 本\n"
                            "study: 勉強\n"
                            "read: 読む\n"
                            "\nNEVER use format 'translation: english_word'\n"
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            "Translate these words (use format 'english: translation'):\n" +
                            "\n".join(batch)
                        )
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
                                f"You are a professional {target_language} translator.\n"
                                "CRITICAL FORMAT RULES:\n"
                                "1. MUST use format 'english: translation'\n"
                                "2. NEVER use any other format\n"
                                "3. NO explanations or labels\n"
                                "4. ONE WORD per line\n"
                                "\nExample format:\n"
                                "anthem: 国歌\n"
                                "and: そして\n"
                                "all: すべて\n"
                                "an: ひとつの\n"
                            )
                        },
                        {
                            "role": "user",
                            "content": (
                                "Translate these words:\n" +
                                "\n".join(failed_words)
                            )
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
                "temperature": 0.1
            }
            
            response = requests.post(self.ollama_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            
            if 'message' in response_data:
                translation_text = response_data['message']['content'].strip()
                print(f"Raw translation response:\n{translation_text}")
                
                translations_dict = {}
                for line in translation_text.split('\n'):
                    line = line.strip()
                    if not line or ':' not in line:
                        continue
                    
                    # Split on first colon only
                    parts = line.split(':', 1)
                    if len(parts) != 2:
                        continue
                    
                    word = parts[0].strip().lower()
                    translation = parts[1].strip()
                    
                    # Skip if the word isn't in our list
                    if word not in [w.lower() for w in words]:
                        continue
                    
                    # Clean up translation
                    translation = translation.strip()
                    translation = re.sub(r'[,.!?]$', '', translation)
                    translation = re.sub(r'\s+.*$', '', translation)  # Remove anything after whitespace
                    
                    # Skip if translation is empty or same as English word
                    if not translation or translation.lower() == word:
                        continue
                    
                    # Japanese-specific validation
                    if target_language == "Japanese":
                        cleaned_translation = ''.join(char for char in translation 
                            if ('\u3040' <= char <= '\u309f' or  # Hiragana
                                '\u30a0' <= char <= '\u30ff' or  # Katakana
                                '\u4e00' <= char <= '\u9fff'))   # Kanji
                        
                        if not cleaned_translation:
                            continue
                        
                        if re.search(r'[a-zA-Z0-9]', cleaned_translation):
                            continue
                        
                        translation = cleaned_translation
                    
                    translations_dict[word] = translation
        
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
            
            return result
        
        except Exception as e:
            print(f"Translation request failed: {str(e)}")
            return [{"original": word, "translation": "[Request failed]"} for word in words]

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
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"Source: {result['url']}")
                        
                        # Add button to show lyrics
                        if st.button(f"Show Lyrics", key=f"lyrics_{i}"):
                            with st.spinner("Fetching lyrics..."):
                                content = agent.get_page_content(result['url'])
                                if content:
                                    st.text_area("Raw Lyrics", value=content, height=300)
                                else:
                                    st.error("Could not fetch lyrics from this source.")
                    
                    with col2:
                        if st.button(f"Analyze Result {i}", key=f"analyze_{i}"):
                            with st.spinner("Fetching and analyzing content..."):
                                content = agent.get_page_content(result['url'])
                                if content:
                                    vocabulary = agent.extract_vocabulary(content)
                                    
                                    # Create two columns for word display
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        # Show most common words first
                                        if vocabulary:
                                            st.write("Most common words:")
                                            word_counts = Counter(content.lower().split())
                                            common_words = sorted(
                                                [(word, count) for word in vocabulary if word in word_counts],
                                                key=lambda x: x[1],
                                                reverse=True
                                            )[:10]
                                            
                                            if st.button("Translate Common Words"):
                                                words_to_translate = [word for word, _ in common_words]
                                                translations, failed_translations = agent.translate_words(
                                                    words_to_translate,
                                                    target_language
                                                )
                                                
                                                if translations:
                                                    st.table({
                                                        "Word": [pair["original"] for pair in translations],
                                                        "Count": [word_counts[pair["original"]] for pair in translations],
                                                        f"{target_language}": [pair["translation"] for pair in translations]
                                                    })
                                                
                                                if failed_translations:
                                                    st.warning("Some translations failed:")
                                                    for fail in failed_translations:
                                                        st.write(f"- {fail['word']}: {fail['reason']}")
                                            
                                            if not successful_translations and not failed_translations:
                                                st.error("Translation failed. Please check if Ollama is running and try again.")
                                                st.code("Run Ollama with: ollama run llama2")
                                    
                                    with col2:
                                        if st.button("Show All Vocabulary"):
                                            with st.spinner("Translating all words..."):
                                                translations, failed_translations = agent.translate_words(
                                                    sorted(vocabulary),
                                                    target_language
                                                )
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
