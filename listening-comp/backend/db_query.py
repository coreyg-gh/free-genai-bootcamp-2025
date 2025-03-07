import chromadb

# Create the client
client = chromadb.PersistentClient(path="/mnt/d/free-genai-bootcamp-2025/local-dev/github/listening-comp/backend/data/vectorstore")

# Get the list of collection names
collection_names = client.list_collections()

# Print collection names
for collection_name in collection_names:
    print(collection_name)

# If you want to access a specific collection, use get_collection()
# For example:
for name in collection_names:
    collection = client.get_collection(name)
    # Now you can work with the collection
    print(f"Collection {name} has {collection.count()} items")