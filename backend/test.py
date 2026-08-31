import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        client_args={"trust_env": False}
    )
)

result = client.models.embed_content(
    model="gemini-embedding-2",
    contents="A Fair Value Gap is a price imbalance between candles.",
    config=types.EmbedContentConfig(
        output_dimensionality=768
    )
)

embedding = result.embeddings[0].values

print("Embedding generated successfully")
print("Dimensions:", len(embedding))
print("First 5 values:", embedding[:5])