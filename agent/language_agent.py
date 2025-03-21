import streamlit as st
import json
import requests
from typing import List, Dict, Optional, Tuple
from duckduckgo_search import DDGS
from html2text import HTML2Text
import time
import re
from collections import Counter
import pandas as pd

# At the top of the file, after other imports
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = {}

class LanguageAgent:
    def __init__(self, host: str = "localhost", port: int = 9000):
        """Initialize the Language Agent with Ollama configuration"""
        self.ollama_url = f"http://{host}:{port}/api/chat"
        self.headers = {'Content-Type': 'application/json'}
        # self.model = "llama3.2:1b"
        # self.model = "mistral:7b"
        self.model = "mistral:7b-instruct-v0.2-q4_K_M"
        # test a model rated by some to be better for translation
        #self.model = "7shi/llama-translate:8b-q4_K_M"

        # Common translations dictionary for fallback
        self.common_translations = {
            "the": "その",
            "that": "それ",
            "and": "そして",
            "you": "あなた",
            "about": "について",
            "when": "いつ",
            "for": "ために",
            "think": "考える",
            "his": "彼の"
        }

        # Language-specific formatting rules
        self.language_formats = {
            "Japanese": """
                Japanese Translation Rules:
                1. Use ONLY kanji with common readings
                2. NO romaji or English characters
                3. NO numbers or special characters
                4. Examples of required format:
                   sundown: 日暮れ
                   the: その
                   that: それ
                   and: そして
                   you: あなた
                   about: について
                   when: いつ
                   for: ために
                   think: 考える
                   his: 彼の
                   sunrise: 日の出
                   sunset: 日没
                   moonlight: 月光
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
    
    def get_page_content(self, url: str) -> Optional[str]:
        """Get content from a webpage."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            h = HTML2Text()
            h.ignore_links = True
            return h.handle(response.text)
        except Exception as e:
            print(f"Error fetching page content: {str(e)}")
            return None

    def extract_vocabulary(self, text: str) -> List[str]:
        """Extract unique words from text."""
        try:
            # Remove special characters and split into words
            words = re.findall(r'\b\w+\b', text.lower())
            # Filter out numbers and short words
            return list(set(word for word in words if len(word) > 2 and not word.isdigit()))
        except Exception as e:
            print(f"Error extracting vocabulary: {str(e)}")
            return []

    def translate_words(self, words: List[str], target_language: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Translate a list of words to the target language using batch processing.
        Returns a tuple of (successful translations, failed translations)
        """
        translated_pairs = []
        batch_size = 5  # Reduce batch size for better quality
        
        # Get language-specific formatting rules
        language_rules = self.language_formats.get(target_language, "")
        
        for i in range(0, len(words), batch_size):
            batch = words[i:i + batch_size]
            
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
                            "5. NEVER include explanations or notes, only respond with the 2 words\n"
                            "6. NO English unless it's the same word in target language\n"
                            "7. ALWAYS provide a translation for every word\n"
                            f"{language_rules}\n"  # Changed from language_specific_format to language_rules
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
                        f"Translate these words to {target_language}. YOU MUST USE THE FORMAT 'word: translation' FOR EVERY WORD:\n" + 
                        "\n".join(batch)
                    )
                }
            ]

            try:
                print(f"\nSending batch: {batch}")
                response = requests.post(
                    self.ollama_url,
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "temperature": 0.3  # Slightly increase temperature for better handling of informal words
                    }
                )
                response.raise_for_status()
                response_data = response.json()
                
                translation_text = response_data["message"]["content"]
                print(f"\nReceived response:\n{translation_text}")
                
                translations_dict = {}
                for line in translation_text.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        word = parts[0].strip().lower()
                        translation = parts[1].strip()
                        translations_dict[word] = translation

                # Process batch results
                batch_results = []
                for word in batch:
                    word_lower = word.lower()
                    if word_lower in translations_dict and translations_dict[word_lower]:
                        batch_results.append({
                            "original": word,
                            "translation": translations_dict[word_lower]
                        })
                    elif word_lower in self.common_translations:  # Use class's common translations
                        batch_results.append({
                            "original": word,
                            "translation": self.common_translations[word_lower]
                        })
                    else:
                        batch_results.append({
                            "original": word,
                            "translation": "[Missing translation]"
                        })
                
                translated_pairs.extend(batch_results)
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"Translation batch failed: {str(e)}")
                for word in batch:
                    translated_pairs.append({
                        "original": word,
                        "translation": f"[Translation failed: {str(e)}]"
                    })

        # Separate successful and failed translations
        successful = [pair for pair in translated_pairs 
                     if not pair["translation"].startswith("[")]
        failed = [{"word": pair["original"], 
                   "reason": pair["translation"][1:-1]}
                  for pair in translated_pairs 
                  if pair["translation"].startswith("[")]

        return successful, failed

    def _try_translation(self, words: List[str], messages: List[Dict[str, str]], target_language: str) -> List[Dict[str, str]]:
        """Helper method to attempt translation with validation."""
        try:
            response_data = self.chat_completion(messages)
            if not response_data:
                return [{"original": word, "translation": "[No response]"} for word in words]
            
            translations_dict = {}
            
            # First pass: exact matches
            for line in response_data.split('\n'):
                line = line.strip()
                if not line or ':' not in line:
                    continue
                
                parts = line.split(':', 1)
                if len(parts) != 2:
                    continue
                
                word = parts[0].strip().lower()
                translation = parts[1].strip()
                
                # Basic cleaning
                translation = re.sub(r'[,.!?]$', '', translation)
                translation = translation.strip()
                
                # Language-specific validation
                if target_language == "Japanese":
                    if not self._validate_japanese(translation):
                        continue
                elif target_language == "Chinese":
                    if not self._validate_chinese(translation):
                        continue
                
                translations_dict[word] = translation
            
            # Second pass: fuzzy matches
            for word in words:
                word_lower = word.lower()
                if word_lower not in translations_dict:
                    # Look for the word as part of other translations
                    for line in response_data.split('\n'):
                        if word_lower in line.lower():
                            parts = line.split(':', 1)
                            if len(parts) == 2:
                                translation = parts[1].strip()
                                translation = re.sub(r'[,.!?]$', '', translation)
                                if self._validate_translation(translation, target_language):
                                    translations_dict[word_lower] = translation
                                    break
            
            # Process results
            result = []
            for word in words:
                word_lower = word.lower()
                if word_lower in translations_dict:
                    result.append({
                        "original": word,
                        "translation": translations_dict[word_lower]
                    })
                else:
                    result.append({
                        "original": word,
                        "translation": "[Missing translation]"
                    })
            
            return result
            
        except Exception as e:
            print(f"Translation request failed: {str(e)}")
            return [{"original": word, "translation": "[Request failed]"} for word in words]

    def _validate_translation(self, translation: str, target_language: str) -> bool:
        """Validate translation based on target language."""
        if target_language == "Japanese":
            return self._validate_japanese(translation)
        elif target_language == "Chinese":
            return self._validate_chinese(translation)
        return bool(translation and not translation.isdigit())

    def _validate_japanese(self, text: str) -> bool:
        """Validate Japanese text."""
        # Check for Japanese characters
        has_japanese = any(
            '\u3040' <= char <= '\u309f' or  # Hiragana
            '\u30a0' <= char <= '\u30ff' or  # Katakana
            '\u4e00' <= char <= '\u9fff'     # Kanji
            for char in text
        )
        # No Latin characters or numbers
        no_latin = not re.search(r'[a-zA-Z0-9]', text)
        return has_japanese and no_latin

    def _validate_chinese(self, text: str) -> bool:
        """Validate Chinese text."""
        # Check for Chinese characters
        has_chinese = any(
            '\u4e00' <= char <= '\u9fff'     # Chinese characters
            for char in text
        )
        # No Latin characters or numbers
        no_latin = not re.search(r'[a-zA-Z0-9]', text)
        return has_chinese and no_latin

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

    def search_web(self, query: str) -> List[Dict[str, str]]:
        """Search the web using DuckDuckGo."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                return [
                    {
                        "title": result["title"],
                        "url": result["href"],  # Changed from "link" to "href"
                        "snippet": result["body"]
                    }
                    for result in results
                ]
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []

def main():
    st.set_page_config(
        page_title="Language Learning Song Assistant",
        page_icon="🎵",
        layout="wide"
    )

    print("Starting main function")  # Debug print

    # Initialize session state
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = {}
    if 'translations' not in st.session_state:
        st.session_state.translations = {}

    st.title("🎵 Language Learning Song Assistant")
    st.markdown("---")

    # Initialize the agent
    agent = LanguageAgent()
    print("Agent initialized")  # Debug print

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
            search_results = agent.search_web(f"{song_title} song information lyrics")
            #search_results = agent.search_web(f"{song_title} song information lyrics meaning")
        if search_results:
            st.subheader("Found relevant information")
            
            # Initialize a flag in session state if not present
            if 'show_translation_buttons' not in st.session_state:
                st.session_state.show_translation_buttons = False

            # Show results and analysis buttons
            for i, result in enumerate(search_results[:3], 1):
                with st.expander(f"Result {i}: {result['title']}", expanded=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"Source: {result['url']}")
                        
                        # Analyze button in the left column
                        if st.button(f"Analyze Result {i}", key=f"analyze_{i}"):
                            print(f"Analyze button clicked for result {i}")
                            with st.spinner("Fetching and analyzing content..."):
                                try:
                                    content = agent.get_page_content(result['url'])
                                    if content:
                                        vocabulary = agent.extract_vocabulary(content)
                                        word_counts = Counter(content.lower().split())
                                        common_words = sorted(
                                            [(word, word_counts[word]) for word in vocabulary if word in word_counts],
                                            key=lambda x: x[1],
                                            reverse=True
                                        )[:10]
                                        
                                        # Store in session state
                                        st.session_state.analysis_data[i] = {
                                            'word_counts': dict(word_counts),
                                            'common_words': common_words,
                                            'all_words': vocabulary
                                        }
                                        st.success(f"Analysis complete! Found {len(vocabulary)} unique words.")
                                except Exception as e:
                                    st.error(f"Error analyzing content: {str(e)}")

                        # After the try-except block, check for analysis data and show translation options
                        if i in st.session_state.analysis_data:
                            st.markdown("#### Translation Options")
                            tcol1, tcol2 = st.columns(2)
                            
                            with tcol1:
                                if st.button("Translate Common Words", key=f"translate_common_{i}", type="primary"):
                                    with st.spinner("Translating common words..."):
                                        words_to_translate = [word for word, _ in st.session_state.analysis_data[i]['common_words']]
                                        translations, failed = agent.translate_words(words_to_translate, target_language)
                                        
                                        # Store translations in session state
                                        if i not in st.session_state.translations:
                                            st.session_state.translations[i] = {}
                                        st.session_state.translations[i]['common'] = translations
                                        
                                        # Display successful translations
                                        if translations:
                                            st.markdown("##### Common Words Translations:")
                                            # Add custom CSS for wider columns and table
                                            st.markdown("""
                                                <style>
                                                .stDataFrame {
                                                    width: 100%;
                                                }
                                                .stDataFrame td:nth-child(1) {
                                                    min-width: 150px;
                                                }
                                                .stDataFrame td:nth-child(2) {
                                                    min-width: 150px;
                                                }
                                                /* Make the table container wider */
                                                [data-testid="stDataFrame"] > div:first-child {
                                                    width: 100%;
                                                    min-width: 400px;
                                                }
                                                </style>
                                            """, unsafe_allow_html=True)
                                            
                                            df_success = pd.DataFrame(
                                                [(t['original'], t['translation']) for t in translations],
                                                columns=['Original', 'Translation']
                                            )
                                            st.dataframe(
                                                df_success,
                                                column_config={
                                                    "Original": st.column_config.TextColumn(width="medium"),
                                                    "Translation": st.column_config.TextColumn(width="medium")
                                                },
                                                hide_index=True,
                                                use_container_width=True,  # Make table use full container width
                                                height=400
                                            )
                                        
                                        # Display failed translations in a separate table
                                        if failed:
                                            st.markdown("##### Failed Translations:")
                                            df_failed = pd.DataFrame(
                                                [(f['word'], f['reason']) for f in failed],
                                                columns=['Word', 'Failure Reason']
                                            )
                                            st.table(df_failed)
                            
                            with tcol2:
                                if st.button("Translate All Words", key=f"translate_all_{i}", type="primary"):
                                    with st.spinner("Translating all words..."):
                                        words_to_translate = st.session_state.analysis_data[i]['all_words'][:100]  # Limit to first 100 words
                                        translations, failed = agent.translate_words(words_to_translate, target_language)
                                        
                                        # Store translations in session state
                                        if i not in st.session_state.translations:
                                            st.session_state.translations[i] = {}
                                        st.session_state.translations[i]['all'] = translations
                                        
                                        # Display successful translations
                                        if translations:
                                            st.markdown("##### All Words Translations:")
                                            # Add custom CSS for wider columns and table
                                            st.markdown("""
                                                <style>
                                                .stDataFrame {
                                                    width: 100%;
                                                }
                                                .stDataFrame td:nth-child(1) {
                                                    min-width: 150px;
                                                }
                                                .stDataFrame td:nth-child(2) {
                                                    min-width: 150px;
                                                }
                                                /* Make the table container wider */
                                                [data-testid="stDataFrame"] > div:first-child {
                                                    width: 100%;
                                                    min-width: 400px;
                                                }
                                                </style>
                                            """, unsafe_allow_html=True)
                                            
                                            df_success = pd.DataFrame(
                                                [(t['original'], t['translation']) for t in translations],
                                                columns=['Original', 'Translation']
                                            )
                                            st.dataframe(
                                                df_success,
                                                column_config={
                                                    "Original": st.column_config.TextColumn(width="medium"),
                                                    "Translation": st.column_config.TextColumn(width="medium")
                                                },
                                                hide_index=True,
                                                use_container_width=True,  # Make table use full container width
                                                height=600
                                            )
                                        
                                        # Display failed translations in a separate table
                                        if failed:
                                            st.markdown("##### Failed Translations:")
                                            df_failed = pd.DataFrame(
                                                [(f['word'], f['reason']) for f in failed],
                                                columns=['Word', 'Failure Reason']
                                            )
                                            st.table(df_failed)

                        # If translations exist for this result, display them
                        if i in st.session_state.translations:
                            # Remove the display of previously translated words
                            pass  # or you can remove this entire if block

                    with col2:
                        # Show Lyrics button
                        if st.button(f"Show Lyrics", key=f"lyrics_{i}"):
                            with st.spinner("Fetching lyrics..."):
                                content = agent.get_page_content(result['url'])
                                if content:
                                    st.text_area("Raw Lyrics", value=content, height=300)
                                else:
                                    st.error("Could not fetch lyrics from this source.")

            # Add translation buttons if we should show them
            if st.session_state.show_translation_buttons:
                st.markdown("---")
                st.subheader("Translation Options")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Translate Common Words", key="translate_common", type="primary"):
                        st.write("Translation of common words will appear here")
                
                with col2:
                    if st.button("Translate All Words", key="translate_all", type="primary"):
                        st.write("Translation of all words will appear here")
        else:
            st.error("No results found for this song. Try another search.")

    # Footer
    st.markdown("---")
    st.markdown("Made with lots of help from AI!")
if __name__ == "__main__":
    main()





























