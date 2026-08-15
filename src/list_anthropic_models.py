import os
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("ANTHROPIC_API_KEY")

print("PROJECT_ROOT:", PROJECT_ROOT)
print("ENV_PATH:", ENV_PATH)
print("ENV_EXISTS:", ENV_PATH.exists())
print("ANTHROPIC_KEY_LOADED:", bool(api_key))

if not api_key:
    raise ValueError(f"ANTHROPIC_API_KEY is missing. Expected .env at: {ENV_PATH}")

client = Anthropic(api_key=api_key)

models = client.models.list()

print("\nAvailable Anthropic model IDs:\n")

for model in models.data:
    print(model.id)