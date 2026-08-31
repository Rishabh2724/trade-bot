import os

from dotenv import load_dotenv
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI,
)
from langchain_core.prompts import ChatPromptTemplate
from pinecone import Pinecone
from app.services.chat_history import get_messages

load_dotenv()


# ---------------------------------------
# Configuration
# ---------------------------------------

PINECONE_NAMESPACE = "trading-v1"

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ---------------------------------------
# Validation
# ---------------------------------------

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is missing")

if not PINECONE_INDEX_NAME:
    raise ValueError("PINECONE_INDEX_NAME is missing")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing")


# ---------------------------------------
# Pinecone
# ---------------------------------------

pc = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pc.Index(
    PINECONE_INDEX_NAME
)


# ---------------------------------------
# Embeddings
# ---------------------------------------

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview",
    output_dimensionality=768,
    client_args={"trust_env": False},
)


# ---------------------------------------
# Gemini
# ---------------------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0.2,
)


# ---------------------------------------
# Prompt
# ---------------------------------------

prompt = ChatPromptTemplate.from_template(
    """
You are TradeCopilot, an AI trading research assistant.

Your job is to answer questions using the provided
knowledge-base context and the conversation history.

IMPORTANT RULES:

1. Use the provided context as your primary source.
2. Use conversation history to understand references
   to previous messages.
3. Do not invent information that is not supported
   by the context.
4. If the context is insufficient, say so clearly.
5. Do not claim that any trading strategy guarantees
   profits.
6. Distinguish research findings from your own
   interpretation.
7. Whenever you make a claim based on a source,
   include its source citation in this format:

   [Source: filename, p. X]

8. Keep the answer structured and easy to understand.

CONVERSATION HISTORY:

{history}


KNOWLEDGE BASE:

{context}


USER QUESTION:

{question}


ANSWER:
"""
)


# ---------------------------------------
# Retrieval
# ---------------------------------------

def retrieve_documents(
    query: str,
    top_k: int = 5,
):

    query_vector = embeddings.embed_query(query)

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=PINECONE_NAMESPACE,
    )

    documents = []

    for match in results.matches or []:

        metadata = match.metadata or {}

        documents.append(
            {
                "text": metadata.get("text", ""),
                "source": metadata.get(
                    "source",
                    "Unknown"
                ),
                "page": metadata.get(
                    "page",
                    "Unknown"
                ),
                "score": match.score,
            }
        )

    return documents


# ---------------------------------------
# RAG
# ---------------------------------------

def ask_trade_copilot(
    question: str,
    conversation_id: str | None = None,
):

    documents = retrieve_documents(question)

    context_parts = []

    for i, document in enumerate(
        documents,
        start=1
    ):

        context_parts.append(
            f"""
SOURCE {i}
File: {document['source']}
Page: {document['page']}

{document['text']}
"""
        )

    context = "\n".join(context_parts)

    # ---------------------------------------
    # Conversation history
    # ---------------------------------------

    history_parts = []

    if conversation_id:

        messages = get_messages(
            conversation_id
        )

        # Exclude the current user message.
        # It is already provided separately below.

        if messages:
            messages = messages[:-1]

        for message in messages:

            role = message["role"].upper()

            history_parts.append(
                f"{role}: {message['content']}"
            )

    history = "\n\n".join(history_parts)

    if not history:

        history = "No previous conversation."

    # ---------------------------------------
    # Prompt
    # ---------------------------------------

    formatted_prompt = prompt.format(
        history=history,
        context=context,
        question=question,
    )

    response = llm.invoke(
        formatted_prompt
    )
    answer = response.content

    if isinstance(answer, list):
        answer = "\n".join(
            item.get("text", str(item))
            if isinstance(item, dict)
            else str(item)
            for item in answer
        )

    return {
        "answer": answer,
        "sources": documents,
    }
# ---------------------------------------
# Test
# ---------------------------------------

if __name__ == "__main__":

    question = (
        "What does the cryptocurrency "
        "trading research say about "
        "technical analysis?"
    )

    result = ask_trade_copilot(question)

    print("\n================================")
    print("TRADE COPILOT")
    print("================================\n")

    print(result["answer"])

    print("\n\nSOURCES")
    print("================================")

    for source in result["sources"]:

        print(
            f"\n{source['source']}"
            f" — Page {source['page']}"
            f" — Score {source['score']}"
        )