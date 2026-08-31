import os

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone


load_dotenv()


# -----------------------------
# Configuration
# -----------------------------

PINECONE_NAMESPACE = "trading-v1"

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is missing from .env")

if not PINECONE_INDEX_NAME:
    raise ValueError("PINECONE_INDEX_NAME is missing from .env")


# -----------------------------
# Pinecone
# -----------------------------

pc = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pc.Index(
    PINECONE_INDEX_NAME
)


# -----------------------------
# Gemini Embeddings
# -----------------------------

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview",
    output_dimensionality=768,
    client_args={"trust_env": False},
)


# -----------------------------
# Test Query
# -----------------------------

query = "What is a bullish Fair Value Gap?"

print(f"\nQuery: {query}")
print("Generating query embedding...")

query_vector = embeddings.embed_query(query)


# -----------------------------
# Pinecone Search
# -----------------------------

results = index.query(
    vector=query_vector,
    top_k=5,
    include_metadata=True,
    namespace=PINECONE_NAMESPACE,
)

matches = results.matches or []


# -----------------------------
# Display Results
# -----------------------------

print("\n================================")
print("RETRIEVAL RESULTS")
print("================================\n")


if not matches:
    print("No relevant documents found.")
    exit()


for i, match in enumerate(matches, start=1):

    metadata = match.metadata or {}

    print(f"RESULT {i}")
    print(f"Score: {match.score}")
    print(
        f"Source: {metadata.get('source', 'Unknown')}"
    )
    print(
        f"Page: {metadata.get('page', 'Unknown')}"
    )

    print("\nContent:")

    content = metadata.get(
        "text",
        "Content not found."
    )

    print(content[:1000])

    print("\n" + "-" * 70 + "\n")