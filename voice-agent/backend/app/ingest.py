from langchain_core.documents import Document
from app.vectorstore import get_vectorstore

with open("data/knowledge.txt", "r", encoding="utf-8") as file:
    content = file.read()

vector_store = get_vectorstore()
vector_store.add_documents([Document(page_content=content, metadata={"source": "knowledge.txt"})])

print("Knowledge added to the vector store successfully.")
