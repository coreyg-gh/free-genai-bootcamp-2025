import chromadb
from chromadb.utils import embedding_functions
import json
import os
import boto3
from typing import Dict, List, Optional

class BedrockEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model_id="amazon.titan-embed-text-v1"):
    #def __init__(self, model_id="amazon.nova-lite-v1:0"):
        """Initialize Bedrock embedding function"""
        print("vector_store - BedrockEmbeddingFunction")
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using Bedrock"""
        print("vector_store - Start of _call_")
        embeddings = []
        for text in texts:
            try:
                print("vector_store - Before invoke_model", str(self.model_id))
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps({
                        "inputText": text
                    })
                )
                response_body = json.loads(response['body'].read())
                embedding = response_body['embedding']
                print("vector_store - Before embeddings.append. ",str(len(embedding)))
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error generating embedding: {str(e)}")
                # Return a zero vector as fallback
                embeddings.append([0.0] * 1536)  # Titan model uses 1536 dimensions
        print("vector_store - Return embeddings vector_store.py __call__")
        return embeddings

class QuestionVectorStore:
    def __init__(self, persist_directory: str = "/mnt/d/free-genai-bootcamp-2025/local-dev/github/listening-comp/backend/data/vectorstore"):
        """Initialize the vector store for JLPT listening questions"""
        print("vector_store - Before persist_directory QuestionVectorStore")
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use Bedrock's Titan embedding model
        print("vector_store - Before BedrockEmbeddingFunction")
        self.embedding_fn = BedrockEmbeddingFunction()
        
        # Create or get collections for each section type
        self.collections = {
            "section2": self.client.get_or_create_collection(
                name="section2_questions",
                embedding_function=self.embedding_fn,
                metadata={"description": "JLPT listening comprehension questions - Section 2"}
            ),
            "section3": self.client.get_or_create_collection(
                name="section3_questions",
                embedding_function=self.embedding_fn,
                metadata={"description": "JLPT phrase matching questions - Section 3"}
            )
        }

    def add_questions(self, section_num: int, questions: List[Dict], video_id: str):
        """Add questions to the vector store"""
        print("vector_store - Start of add_questions")
        if section_num not in [2, 3]:
            raise ValueError("Only sections 2 and 3 are currently supported")

        collection = self.collections[f"section{section_num}"]

        # Initialize lists outside the loop
        ids = []
        documents = []
        metadatas = []
        
        for idx, question in enumerate(questions):
            # Create a unique ID for each question
            question_id = f"{video_id}_{section_num}_{idx}"
            ids.append(question_id)
            
            # Store the full question structure as metadata
            print("vector_store - Before metadatas.append")
            metadatas.append({
                "video_id": video_id,
                "section": section_num,
                "question_index": idx,
                "full_structure": json.dumps(question)
            })
            
            # Create a searchable document from the question content
            if section_num == 2:
                document = f"""
                Situation: {question['Introduction']}
                Dialogue: {question['Conversation']}
                Question: {question['Question']}
                """
            else:  # section 3
                document = f"""
                Situation: {question['Situation']}
                Question: {question['Question']}
                """
            print("vector_store - Before documents.append")
            documents.append(document)
        
        # Log the contents of the lists
        print("IDs:", ids)
        print("Documents:", documents)
        print("Metadatas:", metadatas)
        
        try:
            print("vector_store - Adding to collection.")
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print("vector_store - added to collection okay.")
        except Exception as e:
            print(f"Error adding to collection: {str(e)}")
            raise

    def search_similar_questions(
        self, 
        section_num: int, 
        query: str, 
        n_results: int = 5
       ) -> List[Dict]:
        """Search for similar questions in the vector store"""
        print("vector_store - Start of search_similar_questions")
        print("vector_store - search_similar_questions, section_num: ",str(section_num))
        print("vector_store - search_similar_questions, query: ",str(query))

        if section_num not in [2, 3]:
            print("vector_store search_similar_questions - section_num not in 2,3")
            raise ValueError("Only sections 2 and 3 are currently supported")
        
        collection = self.collections[f"section{section_num}"]
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Convert results to more usable format
        questions = []
        for idx, metadata in enumerate(results['metadatas'][0]):
            question_data = json.loads(metadata['full_structure'])
            question_data['similarity_score'] = results['distances'][0][idx]
            questions.append(question_data)
        print("vector_store search_similar_questions - return questions")    
        return questions

    def get_question_by_id(self, section_num: int, question_id: str) -> Optional[Dict]:
        """Retrieve a specific question by its ID"""
        print("vector_store - Start of get_question_bu_id")
        if section_num not in [2, 3]:
            raise ValueError("Only sections 2 and 3 are currently supported")
            
        collection = self.collections[f"section{section_num}"]
        
        result = collection.get(
            ids=[question_id],
            include=['metadatas']
        )
        
        if result['metadatas']:
            print("vector_store - return result metadatas")
            return json.loads(result['metadatas'][0]['full_structure'])
        return None

    def parse_questions_from_file(self, filename: str) -> List[Dict]:
        """Parse questions from a structured text file"""
        print("vector_store - Start of parse_questions_from_file")
        questions = []
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Split the content into lines
            lines = content.split('\n')
            
            # Create a single question from the entire file content
            question = {
                'Question': 'Analyze the text content',
                'Introduction': '',
                'Conversation': content,
                'Options': []
            }
            
            questions.append(question)
            
            print(f"vector_store - Parsed {len(questions)} questions from {filename}")
            return questions
        except Exception as e:
            print(f"Error parsing questions from {filename}: {str(e)}")
            return []


    def parse_questions_from_file_old(self, filename: str) -> List[Dict]:
        """Parse questions from a structured text file"""
        print("vector_store - Start of parse_questions_from_file")
        questions = []
        current_question = {}
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('<question>'):
                    current_question = {}
                elif line.startswith('Introduction:'):
                    i += 1
                    if i < len(lines):
                        current_question['Introduction'] = lines[i].strip()
                elif line.startswith('Conversation:'):
                    i += 1
                    if i < len(lines):
                        current_question['Conversation'] = lines[i].strip()
                elif line.startswith('Situation:'):
                    i += 1
                    if i < len(lines):
                        current_question['Situation'] = lines[i].strip()
                elif line.startswith('Question:'):
                    i += 1
                    if i < len(lines):
                        current_question['Question'] = lines[i].strip()
                elif line.startswith('Options:'):
                    options = []
                    for _ in range(4):
                        i += 1
                        if i < len(lines):
                            option = lines[i].strip()
                            if option.startswith('1.') or option.startswith('2.') or option.startswith('3.') or option.startswith('4.'):
                                options.append(option[2:].strip())
                    current_question['Options'] = options
                elif line.startswith('</question>'):
                    if current_question:
                        questions.append(current_question)
                        current_question = {}
                i += 1
            print("vector_store - Return questions")
            return questions
        except Exception as e:
            print(f"Error parsing questions from {filename}: {str(e)}")
            return []

    def index_questions_file(self, filename: str, section_num: int):
        """Index all questions from a file into the vector store"""
        # Extract video ID from filename
        print("vector_store - Start of index_questions_file")
        video_id = os.path.basename(filename).split('_section')[0]
        
        # Parse questions from file
        questions = self.parse_questions_from_file(filename)
        
        # Add to vector store
        if questions:
            print("vector_store - if questions check, before add_questions")
            self.add_questions(section_num, questions, video_id)
            print(f"Indexed {len(questions)} questions from {filename}")

if __name__ == "__main__":
    # Example usage
    store = QuestionVectorStore()
    
    # Index questions from files
    question_files = [
        ("backend/data/questions/sY7L5cfCWno_section2.txt", 2),
        ("backend/data/questions/sY7L5cfCWno_section3.txt", 3)
    ]
    
    for filename, section_num in question_files:
        print("vector_store - __main__ for loop for files.")
        if os.path.exists(filename):
            print("vector_store - __main__ os.path.exists")
            store.index_questions_file(filename, section_num)
    
    # Search for similar questions
    similar = store.search_similar_questions(2, "誕生日について質問", n_results=1)
