# Standardization Guide for LLM Interactions & Development

This document outlines the standards, configurations, and best practices for developing LLM-based features in this project. All contractors and contributors must adhere to these guidelines to ensure consistency.

## 1. LLM Configuration & Environment

We use a centralized configuration pattern via `config.py`. **Do not hardcode** model names, API keys, or endpoints.

### Environment Variables
Ensure your `.env` file matches these expectations:

- **`OPENAI_API_BASE`**: The base URL for the LLM provider (e.g., SiliconFlow, OpenAI, DeepSeek).
  - *Default:* `https://api.siliconflow.cn/v1/`
- **`LLM_MODEL`**: The specific model identifier.
  - *Standard:* `deepseek-ai/DeepSeek-V3` (or similar high-reasoning model).
- **`DEEPSEEK_API_KEY`** or **`OPENAI_API_KEY`**: The authentication key.

### Configuration Usage
Access all LLM settings through the `AppConfig` object in `config.py`:

```python
from config import config

# Example Usage
llm = ChatOpenAI(
    model=config.LLM_MODEL_NAME,
    openai_api_key=config.API_KEY,
    openai_api_base=config.LLM_API_BASE,
    temperature=config.LLM_TEMPERATURE  # Standard is 0.3
)
```

## 2. LLM Interaction Standards

### Framework
- Use **LangChain** (`langchain_openai`, `langchain_core`) for all LLM interactions.
- Use **Pydantic** (`pydantic.BaseModel`) to define structured output schemas.

### Prompt Engineering
- **Context:** Always provide rich context (User Profile, Job Data, Local Resources).
- **Persona:** Enforce a consistent persona (e.g., "Singapore Career Coach").
- **Output:** Prefer structured JSON output using `JsonOutputParser` and `Pydantic` models.
- **Tone:** Encouraging, professional, and locally relevant (referencing SkillsFuture, local schemes).

### Example Pattern (Structured Output)

```python
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# 1. Define Output Structure
class DesiredOutput(BaseModel):
    field_one: str = Field(description="Description here")

parser = JsonOutputParser(pydantic_object=DesiredOutput)

# 2. Define Prompt
prompt = PromptTemplate(
    template="Context: {context}\n\nTask: ...\n\n{format_instructions}",
    input_variables=["context"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# 3. Chain
chain = prompt | llm | parser
```

## 3. General Coding Standards

### Style
- **Language:** Python 3.9+
- **Formatting:** Follow PEP 8.
- **Typing:** Use type hints for all function arguments and return values (`List`, `Dict`, `Optional`).
- **Logging:** Use the standard `logging` library. Do not use `print` statements in production code.

### Error Handling
- Wrap LLM calls in `try/except` blocks.
- Log errors using `logger.error()`.
- Provide meaningful fallback responses if the LLM fails (do not crash the app).

## 4. RAG & Embeddings
- **Embeddings:** Configurable via `config.EMBEDDING_MODEL_NAME`.
- **Vector Store:** ChromaDB (local persistence).
- **Document Processing:** Use the existing pipelines in `ingest.py` or `rag_setup.py` rather than creating new ones unless necessary.

## 5. Directory Structure
- **`agents.py`**: Contains higher-level logic and agent definitions.
- **`models.py`**: Database models (SQLAlchemy) and Pydantic schemas.
- **`config.py`**: Central configuration.
- **`company_data/`**: Source documents for RAG.

---
**Note:** If you introduce new dependencies, please update `requirements.txt`.
