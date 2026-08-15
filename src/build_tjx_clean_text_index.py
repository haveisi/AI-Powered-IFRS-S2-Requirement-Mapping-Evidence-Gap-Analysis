from pathlib import Path

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TEXT_DIR = PROJECT_ROOT / "03_Extracted_Text"
INDEX_DIR = PROJECT_ROOT / "storage" / "tjx_clean_text_index"

INDEX_DIR.mkdir(parents=True, exist_ok=True)

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

splitter = SentenceSplitter(
    chunk_size=800,
    chunk_overlap=100
)

print("Loading clean TJX text...")

documents = SimpleDirectoryReader(
    input_files=[str(TEXT_DIR / "tjx_2025_clean_text.txt")]
).load_data()

print(f"Loaded {len(documents)} clean text document(s).")

print("Building clean text index...")

index = VectorStoreIndex.from_documents(
    documents,
    transformations=[splitter]
)

print("Saving clean text index...")

index.storage_context.persist(
    persist_dir=str(INDEX_DIR)
)

print(f"Clean text index saved to: {INDEX_DIR}")