from app.llm import generate_text
from app.vector_store import get_vector_store

retreiver = get_vector_store().as_retriever(search_kwargs={"k": 3})

SYSTEM_PROMPT = """You are a helpful assistant that provides Soultions to business from manual work to automation. You have access to the following tools:
- You have access to a vector store that contains information about business solutions and automation. You can use this to provide relevant information to the user.
- You can provide information about business solutions and automation based on the user's query."""

def ask_question(question: str, history=None):
    if history is None:
        history = []
    documents = retreiver.invoke(question)
    context = "\n".join(document.page_content.strip() for document in documents if document.page_content)
    conversation = "\n".join(
          f"{message.get('role', 'user')}: {message.get('content', '')}"
          for message in history[-10:]
      )
    prompt = f"""
    {SYSTEM_PROMPT}

    Conversation history:
    {conversation}

    Retrieved knowledge:
    {context or "No relevant knowledge found."}

    Current user question:
    {question}

    Answer:
    """ 
    return generate_text(prompt)