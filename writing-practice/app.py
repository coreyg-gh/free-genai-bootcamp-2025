import streamlit as st
import requests
from enum import Enum
import json
from typing import Optional, List, Dict
import openai
import logging
import random
import os

# Setup Custom Logging -----------------------
# Create a custom logger for your app only
logger = logging.getLogger('my_app')
logger.setLevel(logging.DEBUG)

# Remove any existing handlers to prevent duplicate logging
if logger.hasHandlers():
    logger.handlers.clear()

# Create file handler
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - MY_APP - %(message)s')
fh.setFormatter(formatter)

# Add handler to logger
logger.addHandler(fh)

# Prevent propagation to root logger
logger.propagate = False

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# State Management
class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"

class JapaneseLearningApp:
    def __init__(self):
        logger.debug("Initializing Japanese Learning App...")
        self.initialize_session_state()
        self.load_vocabulary()
        
    def initialize_session_state(self):
        """Initialize or get session state variables"""
        if 'app_state' not in st.session_state:
            st.session_state.app_state = AppState.SETUP
        if 'current_sentence' not in st.session_state:
            st.session_state.current_sentence = ""
        if 'review_data' not in st.session_state:
            st.session_state.review_data = None
            
    def load_vocabulary(self):
        """Fetch vocabulary from API using group_id"""
        try:
            # Get group_id from query parameters
            group_id = st.query_params.get('group_id', '1')  # Default to '1' if not provided
            
            logger.debug(f"Attempting to load vocabulary with group_id: {group_id}")
            
            # Make API request with correct endpoint
            url = f'http://localhost:5000/groups/{group_id}/words/raw'
            logger.debug(f"Making API request to: {url}")
            
            response = requests.get(url)
            logger.debug(f"API Response status: {response.status_code}")
            logger.debug(f"API Response content: {response.text[:200]}...")  # Log first 200 chars of response
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"Successfully parsed JSON. Items count: {len(data.get('items', []))}")
                    self.vocabulary = {'words': data.get('items', [])}  # Restructure the data to match expected format
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    st.error(f"Invalid JSON response from API: {response.text[:200]}")
                    self.vocabulary = None
            else:
                logger.error(f"API request failed: {response.status_code}")
                st.error(f"API request failed with status code: {response.status_code}")
                self.vocabulary = None
        except Exception as e:
            logger.error(f"Failed to load vocabulary: {str(e)}")
            st.error(f"Failed to load vocabulary: {str(e)}")
            self.vocabulary = None

    def generate_sentence(self, word: dict) -> str:
        """Generate a sentence using OpenAI API"""
        # Get japanese word from the dictionary, falling back to different fields
        japanese_word = word.get('japanese', word.get('kanji', ''))
        
        logger.debug(f"Generating sentence for word: {japanese_word}")
        logger.debug(f"Full word data: {word}")
        
        prompt = f"""Generate a simple Japanese sentence using the word '{japanese_word}'.
        The grammar should be scoped to JLPTN5 grammar.
        You can use the following vocabulary to construct a simple sentence:
        - simple objects eg. book, car, ramen, sushi
        - simple verbs, to drink, to eat, to meet
        - simple times eg. tomorrow, today, yesterday
        
        Please provide the response in this format:
        Japanese: [sentence in kanji/hiragana]
        English: [English translation]
        """
        
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            generated_text = response.choices[0].message.content.strip()
            logger.debug(f"Generated response from OpenAI: {generated_text}")
            return generated_text
        except Exception as e:
            logger.error(f"Error generating sentence with OpenAI: {str(e)}")
            raise

    def grade_submission(self, image) -> Dict:
        """Process image submission and grade it"""
        # TODO: Implement MangaOCR integration
        # For now, return mock data
        return {
            "transcription": "今日はラーメンを食べます",
            "translation": "I will eat ramen today",
            "grade": "S",
            "feedback": "Excellent work! The sentence accurately conveys the meaning."
        }

    def render_setup_state(self):
        """Render the setup state UI"""
        logger.debug("Entering render_setup_state")
        
        # Display vocabulary status
        if self.vocabulary and self.vocabulary.get('words'):
            word_count = len(self.vocabulary['words'])
            logger.debug(f"Loaded vocabulary with {word_count} words")
            st.write(f"Loaded {word_count} words")
            
            # Generate sentence button
            if st.button("Generate Sentence", key="generate_btn"):
                logger.debug("Generate button clicked")
                word = random.choice(self.vocabulary['words'])
                sentence = self.generate_sentence(word)
                
                if sentence:
                    st.session_state.current_sentence = sentence
                    if st.button("Continue to Practice"):
                        st.session_state.app_state = AppState.PRACTICE
                        st.experimental_rerun()
        else:
            logger.warning("No vocabulary loaded")
            st.error("No vocabulary loaded. Please check your connection to the API.")
            if st.button("Retry Loading"):
                self.load_vocabulary()
                st.experimental_rerun()

    def render_practice_state(self):
        """Render the practice state UI"""
        st.title("Practice Japanese")
        st.write(f"English Sentence: {st.session_state.current_sentence}")
        
        uploaded_file = st.file_uploader("Upload your written Japanese", type=['png', 'jpg', 'jpeg'])
        
        if st.button("Submit for Review") and uploaded_file:
            st.session_state.review_data = self.grade_submission(uploaded_file)
            st.session_state.app_state = AppState.REVIEW
            st.experimental_rerun()

    def render_review_state(self):
        """Render the review state UI"""
        st.title("Review")
        st.write(f"English Sentence: {st.session_state.current_sentence}")
        
        review_data = st.session_state.review_data
        st.subheader("Your Submission")
        st.write(f"Transcription: {review_data['transcription']}")
        st.write(f"Translation: {review_data['translation']}")
        st.write(f"Grade: {review_data['grade']}")
        st.write(f"Feedback: {review_data['feedback']}")
        
        if st.button("Next Question"):
            st.session_state.app_state = AppState.SETUP
            st.session_state.current_sentence = ""
            st.session_state.review_data = None
            st.experimental_rerun()

    def run(self):
        """Main method to run the app"""
        logger.debug("Running app...")
        
        # Basic app structure
        st.title("Japanese Writing Practice")
        
        # Show current state for debugging
        logger.debug(f"Current app state: {st.session_state.app_state}")
        logger.debug(f"Vocabulary loaded: {self.vocabulary is not None}")
        
        # Render appropriate state
        if st.session_state.app_state == AppState.SETUP:
            self.render_setup_state()
        elif st.session_state.app_state == AppState.PRACTICE:
            self.render_practice_state()
        elif st.session_state.app_state == AppState.REVIEW:
            self.render_review_state()

# Run the app
if __name__ == "__main__":
    app = JapaneseLearningApp()
    app.run()