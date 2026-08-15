from pathlib import Path

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "01_Source_Documents"
INDEX_DIR = PROJECT_ROOT / "storage" / "tjx_index"

INDEX_DIR.mkdir(parents=True, exist_ok=True)

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

print("Loading TJX report...")
documents = SimpleDirectoryReader(
    input_dir=str(SOURCE_DIR),
    recursive=True
).load_data()

print(f"Loaded {len(documents)} document(s).")

print("Building index...")
index = VectorStoreIndex.from_documents(documents)

print("Saving index...")
index.storage_context.persist(persist_dir=str(INDEX_DIR))

print(f"Index saved to: {INDEX_DIR}")