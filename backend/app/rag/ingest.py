import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone

# ---------------------------------------
# Environment
# ---------------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is missing")

if not PINECONE_INDEX_NAME:
    raise ValueError("PINECONE_INDEX_NAME is missing")

# ---------------------------------------
# Paths
# ---------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

PDF_DIRECTORY = BASE_DIR / "data" / "pdfs"

# ---------------------------------------
# Pinecone
# ---------------------------------------

PINECONE_NAMESPACE = "trading-v1"

pc = Pinecone(api_key=PINECONE_API_KEY)

index = pc.Index(PINECONE_INDEX_NAME)

# ---------------------------------------
# Gemini Embeddings
# ---------------------------------------

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview",
    output_dimensionality=768,
)


def embed_documents_with_retry(texts, max_attempts=5):
    delay = 5

    for attempt in range(1, max_attempts + 1):
        try:
            return embeddings.embed_documents(texts)
        except Exception as error:
            error_text = str(error)
            if "429" not in error_text and "RESOURCE_EXHAUSTED" not in error_text:
                raise

            retry_match = re.search(r"retryDelay['\"]?[:=]\s*'?([0-9]+)s?", error_text)
            if retry_match:
                delay = int(retry_match.group(1))

            if attempt == max_attempts:
                raise

            print(
                f"Embedding rate-limited, retrying in {delay} seconds "
                f"(attempt {attempt}/{max_attempts})..."
            )
            time.sleep(delay)
            delay = min(delay * 2, 300)

# ---------------------------------------
# Load PDFs
# ---------------------------------------

documents = []

pdf_files = list(PDF_DIRECTORY.glob("*.pdf"))

if not pdf_files:
    raise FileNotFoundError(
        f"No PDFs found in {PDF_DIRECTORY}"
    )

print(f"\nFound {len(pdf_files)} PDFs\n")

for pdf_file in pdf_files:

    print(f"Loading: {pdf_file.name}")

    loader = PyPDFLoader(str(pdf_file))

    pdf_documents = loader.load()

    for document in pdf_documents:
        document.metadata["source"] = pdf_file.name
        document.metadata["file_type"] = "pdf"

    documents.extend(pdf_documents)

    print(
        f"  Loaded {len(pdf_documents)} pages"
    )

print(f"\nTotal pages: {len(documents)}")

# ---------------------------------------
# Split into chunks
# ---------------------------------------

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
)

chunks = text_splitter.split_documents(documents)

print(f"Total chunks: {len(chunks)}")

# ---------------------------------------
# Upload to Pinecone
# ---------------------------------------

print("\nUploading vectors...\n")

batch_size = 50
uploaded_count = 0

for start in range(
    0,
    len(chunks),
    batch_size
):

    batch_chunks = chunks[
        start:start + batch_size
    ]

    batch_texts = []
    batch_metadata = []

    for chunk in batch_chunks:
        text = chunk.page_content.strip()

        if not text:
            continue

        batch_texts.append(text)
        batch_metadata.append(
            {
                "text": text,
                "source": chunk.metadata.get(
                    "source",
                    "unknown"
                ),
                "page": chunk.metadata.get(
                    "page",
                    0
                ),
                "file_type": "pdf",
            }
        )

    if not batch_texts:
        continue

    batch_vectors = embed_documents_with_retry(batch_texts)

    batch = []

    for offset, (metadata, vector) in enumerate(zip(batch_metadata, batch_vectors)):
        vector_id = (
            f"{metadata['source']}-"
            f"{metadata['page']}-"
            f"{start + offset}"
        )

        batch.append(
            {
                "id": vector_id,
                "values": vector,
                "metadata": metadata,
            }
        )

    index.upsert(
        vectors=batch,
        namespace=PINECONE_NAMESPACE
    )

    uploaded_count += len(batch)

    print(
        f"Uploaded {uploaded_count}/{len(chunks)}"
    )

# ---------------------------------------
# Done
# ---------------------------------------

print("\n================================")
print("INGESTION COMPLETE")
print("================================")

print(f"PDFs: {len(pdf_files)}")
print(f"Chunks: {uploaded_count}")
print(f"Index: {PINECONE_INDEX_NAME}")
print(f"Namespace: {PINECONE_NAMESPACE}")