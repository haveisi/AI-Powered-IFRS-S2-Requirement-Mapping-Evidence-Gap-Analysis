import os
from pathlib import Path
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


# -------------------------------------------------------
# 1. Define project paths
# -------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "01_Source_Documents"
OUTPUT_DIR = PROJECT_ROOT / "03_Extracted_Text"
ENV_PATH = PROJECT_ROOT / ".env"

OUTPUT_DIR.mkdir(exist_ok=True)


# -------------------------------------------------------
# 2. Load Anthropic API key
# -------------------------------------------------------
load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("ANTHROPIC_API_KEY")

print("PROJECT_ROOT:", PROJECT_ROOT)
print("ENV_PATH:", ENV_PATH)
print("ENV_EXISTS:", ENV_PATH.exists())
print("ANTHROPIC_API_KEY_LOADED:", bool(api_key))

if not api_key:
    raise ValueError(
        f"ANTHROPIC_API_KEY is missing. Expected .env file at: {ENV_PATH}"
    )


# -------------------------------------------------------
# 3. Set Claude as LLM and HuggingFace as embedding model
# -------------------------------------------------------
Settings.llm = Anthropic(
    model="claude-3-5-haiku-latest",
    temperature=0
)

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)


# -------------------------------------------------------
# 4. Load TJX report PDF
# -------------------------------------------------------
documents = SimpleDirectoryReader(
    input_dir=str(SOURCE_DIR),
    recursive=True
).load_data()

print(f"Loaded {len(documents)} document chunks/pages.")


# -------------------------------------------------------
# 5. Create searchable index
# -------------------------------------------------------
index = VectorStoreIndex.from_documents(documents)


# -------------------------------------------------------
# 6. Create query engine
# -------------------------------------------------------
query_engine = index.as_query_engine(
    similarity_top_k=6
)


# -------------------------------------------------------
# 7. Ask ESG question
# -------------------------------------------------------
question = """
What are the main sustainability topics discussed in the TJX 2025 Global Corporate Responsibility Report?

Give a concise answer using only information from the report.
Also identify which topics may require human review before being used in formal ESG reporting.
"""

response = query_engine.query(question)


# -------------------------------------------------------
# 8. Print result
# -------------------------------------------------------
print("\nQUESTION:")
print(question)

print("\nANSWER:")
print(response)

print("\nSOURCE EVIDENCE:")
for i, source_node in enumerate(response.source_nodes, start=1):
    print(f"\n--- Source {i} ---")
    print(source_node.node.get_content()[:1200])

print("\n" + "=" * 80)
print("QUESTION")
print("=" * 80)
print(question)

print("\n" + "=" * 80)
print("ANSWER")
print("=" * 80)
print(response)

print("\n" + "=" * 80)
print("SOURCE EVIDENCE")
print("=" * 80)

for i, source_node in enumerate(response.source_nodes, start=1):
    print(f"\n--- Source {i} ---")
    print(source_node.node.get_content()[:1200])


output_path = OUTPUT_DIR / "tjx_llamaindex_result.txt"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("QUESTION:\n")
    f.write(question)

    f.write("\n\nANSWER:\n")
    f.write(str(response))

    f.write("\n\nSOURCE EVIDENCE:\n")
    for i, source_node in enumerate(response.source_nodes, start=1):
        f.write(f"\n--- Source {i} ---\n")
        f.write(source_node.node.get_content()[:1200])
        f.write("\n")

print(f"\nSaved result to: {output_path}")
# -------------------------------------------------------
# 9. Save result
# -------------------------------------------------------
output_path = OUTPUT_DIR / "tjx_llamaindex_anthropic_answer.txt"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("QUESTION:\n")
    f.write(question)
    f.write("\n\nANSWER:\n")
    f.write(str(response))
    f.write("\n\nSOURCE EVIDENCE:\n")

    for i, source_node in enumerate(response.source_nodes, start=1):
        f.write(f"\n--- Source {i} ---\n")
        f.write(source_node.node.get_content()[:1200])
        f.write("\n")

print(f"\nSaved output to: {output_path}")