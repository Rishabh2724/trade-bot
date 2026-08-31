import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

PINECONE_NAMESPACE = "trading-v1"

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME_RAW = os.getenv("PINECONE_INDEX_NAME")
PINECONE_INDEX_NAME = (
    PINECONE_INDEX_NAME_RAW.replace("_", "-")
    if PINECONE_INDEX_NAME_RAW
    else None
)

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is missing from .env")

if not PINECONE_INDEX_NAME:
    raise ValueError("PINECONE_INDEX_NAME is missing from .env")

if PINECONE_INDEX_NAME_RAW and PINECONE_INDEX_NAME_RAW != PINECONE_INDEX_NAME:
    print(
        f"Normalizing Pinecone index name from {PINECONE_INDEX_NAME_RAW} to {PINECONE_INDEX_NAME}"
    )

pc = Pinecone(
    api_key=PINECONE_API_KEY
)

if not pc.has_index(PINECONE_INDEX_NAME):
    available_indexes = [item.name for item in pc.list_indexes()]
    raise ValueError(
        f"Pinecone index {PINECONE_INDEX_NAME!r} does not exist. Available indexes: {available_indexes}"
    )

index = pc.Index(PINECONE_INDEX_NAME)

print("Index stats:")
print(index.describe_index_stats())

print("\nGetting vector IDs...")

vector_ids = []

for item in index.list(
    namespace=PINECONE_NAMESPACE,
    limit=5
):
    print("Item:", item)

    if isinstance(item, str):
        vector_ids.append(item)
    elif isinstance(item, dict):
        if "id" in item:
            vector_ids.append(item["id"])
        elif "vectors" in item:
            vector_ids.extend(
                vector["id"]
                for vector in item["vectors"]
            )
    elif hasattr(item, "vectors"):
        vector_ids.extend(
            vector.id
            for vector in item.vectors
            if getattr(vector, "id", None)
        )
    elif hasattr(item, "id"):
        vector_ids.append(item.id)

print("\nVector IDs:")
for vector_id in vector_ids:
    print(vector_id)

if not vector_ids:
    raise RuntimeError(f"No vector IDs found in namespace {PINECONE_NAMESPACE!r}")

known_id = "2003.11352v5.pdf-0-367"

if known_id in vector_ids:
    fetch_id = known_id
else:
    fetch_id = vector_ids[0]

print(f"\nFetching vector: {fetch_id}...")

result = index.fetch(
    ids=[fetch_id],
    namespace=PINECONE_NAMESPACE
)

print("\nFetched vector:")
print(result)