The final submission application uses the opea-comps/mega-server-new container services.

Video walkthrough of application:
https://youtu.be/HZKq2T1IPdo

The apps run in the n8n-server container with the main entry point being:
http://localhost:5678/webhook/language-hub

The following services are the main ones used:
- ollama for translation, random word selection, checking guessed word
- speecht5 for audio generation
- pollinations.ai for image generation

I have saved the n8n workflows as json files.  I was unable to upload the n8n_data sql database due to previously testing with a HF api key and could not find how to delete it from the older db entries even though it was no longer saved in any nodes.  Please let me know if I should share within n8n or some other means.

AI generated descriptions of the workflow files:
- Language_Learning_Hub.json: An n8n workflow for language learning automation (e.g., vocabulary retrieval, translation, or integration with learning platforms).
- Song_Learning_App.json: An n8n workflow for music-related automation (e.g., fetching song lyrics, integrating with music APIs, or user engagement features).
- Vocabulary_Image_Game.json: An n8n workflow that may automate vocabulary quizzes with image associations (e.g., retrieving images for words, game logic, or user progress tracking)

