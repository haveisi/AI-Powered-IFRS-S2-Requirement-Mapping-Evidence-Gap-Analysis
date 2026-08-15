from pathlib import Path

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


# -------------------------------------------------------
# 1. Project paths
# -------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = PROJECT_ROOT / "storage" / "tjx_index"


# -------------------------------------------------------
# 2. Force local HuggingFace embeddings
#    This prevents LlamaIndex from trying OpenAI embeddings.
# -------------------------------------------------------
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)


# -------------------------------------------------------
# 3. Load saved index
# -------------------------------------------------------
print("Loading saved TJX index...")

storage_context = StorageContext.from_defaults(
    persist_dir=str(INDEX_DIR)
)

index = load_index_from_storage(
    storage_context=storage_context,
    embed_model=Settings.embed_model
)


# -------------------------------------------------------
# 4. Retrieve evidence only — no Claude, no OpenAI
# -------------------------------------------------------
retriever = index.as_retriever(similarity_top_k=3)

question = """
What sustainability topics does TJX discuss related to climate, energy,
emissions, supply chain, governance, and human capital?
"""

nodes = retriever.retrieve(question)


# -------------------------------------------------------
# 5. Print retrieved chunks
# -------------------------------------------------------
print("\nRetrieved evidence chunks:\n")

for i, node in enumerate(nodes, start=1):
    print(f"\n--- Chunk {i} ---")
    print(node.node.get_content()[:1500])