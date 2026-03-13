# Custom LLM Endpoint Setup (When Groq is Restricted)

When Groq API is blocked in your network (e.g. corporate firewall), you can use an alternative LLM endpoint like **TCS genailab**. Follow the manual changes below.

---

## Overview of Changes

1. **Config** (`backend/config.py`) – Add new environment variables
2. **Classifier** (`backend/detection/classifier.py`) – Use custom endpoint when configured
3. **Requirements** (`requirements.txt`) – Add `langchain-openai`
4. **.env** – Add your endpoint credentials

---

## 1. Edit `backend/config.py`

**Find this section** (around line 10):

```python
class Settings(BaseSettings):
    """Application settings loaded from environment."""

    groq_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./moderation.db"
```

**Replace with:**

```python
class Settings(BaseSettings):
    """Application settings loaded from environment."""

    groq_api_key: str = ""
    # Alternative LLM (when Groq is restricted) - e.g. TCS genailab
    llm_base_url: str = ""  # e.g. https://genailab.tcs.in/v1
    llm_model: str = ""  # e.g. azure_ai/genailab-maas-DeepSeek-V3-0324
    llm_api_key: str = ""
    ssl_verify: bool = True  # Set False for corporate proxy/SSL issues
    database_url: str = "sqlite+aiosqlite:///./moderation.db"
```

---

## 2. Edit `backend/detection/classifier.py`

### Step A – Update imports (top of file)

**Find:**
```python
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
```

**Replace with:**
```python
import httpx
from langchain_core.prompts import ChatPromptTemplate
```

(Keep the rest of the imports as-is.)

---

### Step B – Update the `HarassmentClassifier` class `__init__` method

**Find this block** (around lines 55–67):

```python
class HarassmentClassifier:
    """Uses Groq LLM to classify content for harassment."""

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        settings = get_settings()
        self._client = ChatGroq(
            api_key=settings.groq_api_key,
            model=model_name,
            temperature=0.1,
        )
        self._prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
        self._parser = JsonOutputParser()
```

**Replace with:**

```python
class HarassmentClassifier:
    """Uses LLM (Groq or custom endpoint) to classify content for harassment."""

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        settings = get_settings()

        if settings.llm_base_url and settings.llm_model and settings.llm_api_key:
            # Custom endpoint (e.g. TCS genailab) when Groq is restricted
            from langchain_openai import ChatOpenAI

            http_client = httpx.Client(verify=settings.ssl_verify)
            self._client = ChatOpenAI(
                base_url=settings.llm_base_url.rstrip("/"),
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                temperature=0.1,
                http_client=http_client,
            )
            logger.info("Using custom LLM endpoint: %s", settings.llm_base_url)
        else:
            # Default: Groq
            from langchain_groq import ChatGroq

            self._client = ChatGroq(
                api_key=settings.groq_api_key,
                model=model_name,
                temperature=0.1,
            )
            logger.info("Using Groq LLM")

        self._prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
        self._parser = JsonOutputParser()
```

---

## 3. Edit `requirements.txt`

**Find:**
```
langchain-groq>=0.0.6
langchain-core>=0.1.0
```

**Add this line** after `langchain-groq`:
```
langchain-openai>=0.0.5
```

Result:
```
langchain-groq>=0.0.6
langchain-openai>=0.0.5
langchain-core>=0.1.0
```

---

## 4. Edit `.env`

Add these lines (use your actual values):

```
# Custom LLM endpoint (when Groq is restricted)
LLM_BASE_URL=https://genailab.tcs.in/v1
LLM_MODEL=azure_ai/genailab-maas-DeepSeek-V3-0324
LLM_API_KEY=your_api_key_here
SSL_VERIFY=false
```

| Variable     | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| `LLM_BASE_URL` | Your endpoint base URL. Try with or without `/v1` if one doesn’t work.   |
| `LLM_MODEL`   | Model name, e.g. `azure_ai/genailab-maas-DeepSeek-V3-0324`              |
| `LLM_API_KEY` | Your API key                                                             |
| `SSL_VERIFY`  | Set to `false` if you have SSL/proxy issues                              |

---

## 5. Install the new dependency

```cmd
venv\Scripts\activate
pip install langchain-openai
```

Or reinstall everything:

```cmd
pip install -r requirements.txt
```

---

## 6. Run the application

```cmd
python run.py
```

Then open http://localhost:8000/dashboard

---

## Troubleshooting

| Issue                         | Suggestion                                                                 |
|------------------------------|----------------------------------------------------------------------------|
| Connection error             | Check `LLM_BASE_URL`. Try `https://genailab.tcs.in` with and without `/v1` |
| SSL / certificate error      | Set `SSL_VERIFY=false` in `.env`                                          |
| Wrong model / API format     | Confirm `LLM_MODEL` with your provider                                    |
| Still using Groq             | Ensure `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` are all set          |

---

## Reverting to Groq

To use Groq again, either:

1. Remove or comment out `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` in `.env`,  
   **or**
2. Delete those three lines from `.env`.

Then ensure `GROQ_API_KEY` is set in `.env`.
