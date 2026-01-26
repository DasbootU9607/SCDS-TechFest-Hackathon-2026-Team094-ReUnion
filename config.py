import os
from dotenv import load_dotenv

# Load environment variables (for sensitive keys)
load_dotenv()

class AppConfig:
    # --- LLM Configuration (Public/Non-Sensitive) ---
    # These control which models and endpoints the application uses.
    
    # Base URL for the LLM Provider (e.g., SiliconFlow, DeepSeek, OpenAI)
    LLM_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.siliconflow.cn/v1/")
    
    # Model used for Chat, Reasoning, and Roadmap generation
    # Examples: "deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-7B-Instruct", "gpt-4o"
    LLM_MODEL_NAME = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3")
    
    # Model used for generating Vector Embeddings (RAG)
    # Examples: "BAAI/bge-m3", "text-embedding-3-small"
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    
    # Temperature for creativity (0.0 = deterministic, 1.0 = creative)
    LLM_TEMPERATURE = 0.3

    # --- Sensitive Keys (Loaded from environment only) ---
    @property
    def API_KEY(self):
        # Checks for various common key names
        return os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

# Global Instance
config = AppConfig()
