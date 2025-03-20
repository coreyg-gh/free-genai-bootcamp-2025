import json
import requests
from typing import List, Dict
from duckduckgo_search import DDGS
from html2text import HTML2Text

class LanguageAgent:
    def __init__(self, host: str = "localhost", port: int = 9000):
        self.ollama_url = f"http://{host}:{port}/api/chat"
        self.headers = {'Content-Type': 'application/json'}
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
        batch_size = 20  # Process 20 words at a time
        
        # Process words in batches
        for i in range(0, len(words), batch_size):
            batch = words[i:i + batch_size]
            
            # Create a prompt for translation
            messages = [
                {
                    "role": "system",
                    "content": f"You are a translator. Translate each word to {target_language}. "
                              "Respond with one translation per line in the format: word: translation"
                },
                {
                    "role": "user",
                    "content": f"Translate these words to {target_language}: {', '.join(batch)}"
                }
            ]
            
            translation_response = self.chat_completion(messages)
            if translation_response:
                # Process the response into word pairs
                lines = translation_response.strip().split('\n')
                for word, line in zip(batch, lines):
                    # Clean up the response and create a word pair
                    translation = line.strip().split(':')[-1].strip()
                    translated_pairs.append({
                        "original": word,
                        "translation": translation
                    })
                    
        return translated_pairs

    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            outputs = []
            for line in response.content.splitlines():
                if line.strip():
                    try:
                        response_data = json.loads(line)
                        if 'message' in response_data:
                            outputs.append(response_data['message'].get('content', ''))
                    except json.JSONDecodeError:
                        continue
            
            return ''.join(outputs)
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            print(f"URL attempted: {self.ollama_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            return None

def main():
    agent = LanguageAgent()
    
    # Get language preference
    print("\nWelcome to the Language Learning Song Assistant!")
    print("------------------------------------------------")
    target_language = input("Enter the language you want translations in (e.g., Spanish, French, German): ")
    song_title = input("Enter a song title to search for: ")
    
    print(f"\nSearching for information about: {song_title}")
    
    # Search for general information about the song
    search_results = agent.search_web(f"{song_title} song information lyrics meaning")
    
    if search_results:
        print("\nFound relevant information:")
        for i, result in enumerate(search_results[:3], 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            
            # Ask if user wants to analyze this result
            analyze = input(f"\nWould you like to analyze result {i}? (y/n): ").lower()
            if analyze == 'y':
                print("\nFetching and analyzing content...")
                content = agent.get_page_content(result['url'])
                
                if not content:
                    print("Could not retrieve content from this source. Would you like to try another result?")
                    continue
                    
                vocabulary = agent.extract_vocabulary(content)
                if not vocabulary:
                    print("No processable text found in this content. Would you like to try another result?")
                    continue
                    
                print(f"\nUnique words found: {len(vocabulary)}")
                
                # Show sample of vocabulary with translations
                print(f"\nSample vocabulary (first 10 words) with {target_language} translations:")
                sample_words = sorted(vocabulary)[:10]
                translations = agent.translate_words(sample_words, target_language)
                for pair in translations:
                    print(f"- {pair['original']} : {pair['translation']}")
                
                # Ask if user wants to see more vocabulary
                more = input("\nWould you like to see more vocabulary? (y/n): ").lower()
                if more == 'y':
                    print(f"\nAll unique words with {target_language} translations:")
                    translations = agent.translate_words(sorted(vocabulary), target_language)
                    for pair in translations:
                        print(f"- {pair['original']} : {pair['translation']}")
    else:
        print("No results found for this song. Try another search.")

    # Ask if user wants to search for another song
    another = input("\nWould you like to search for another song? (y/n): ").lower()
    if another == 'y':
        main()  # Recursive call to start over
    else:
        print("\nThank you for using the Language Learning Song Assistant!")

if __name__ == "__main__":
    main()




