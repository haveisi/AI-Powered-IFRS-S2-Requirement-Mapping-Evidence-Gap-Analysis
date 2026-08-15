from pathlib import Path

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = PROJECT_ROOT / "storage" / "tjx_clean_text_index"

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

print("Loading saved clean TJX index...")

storage_context = StorageContext.from_defaults(
    persist_dir=str(INDEX_DIR)
)

index = load_index_from_storage(
    storage_context=storage_context,
    embed_model=Settings.embed_model
)

retriever = index.as_retriever(similarity_top_k=3)

question = """
What sustainability topics does TJX discuss related to climate, energy,
emissions, supply chain, governance, and human capital?
"""

nodes = retriever.retrieve(question)

print("\nRetrieved evidence chunks:\n")

for i, node in enumerate(nodes, start=1):
    print(f"\n--- Clean Chunk {i} ---")
    print(node.node.get_content()[:1500])