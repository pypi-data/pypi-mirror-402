# Alchemyst LangChain

Persistent memory for LangChain powered by Alchemyst AI.

---

## Installation

```bash
pip install alchemyst-langchain
```

---

## Quick Start

```python
from alchemyst_langchain import AlchemystMemory
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI

# Create persistent memory
memory = AlchemystMemory(
    api_key="your-alchemyst-api-key",
    session_id="user-123"
)

# Use with LangChain
llm = ChatOpenAI(model="gpt-4o-mini")
chain = ConversationChain(llm=llm, memory=memory)

# Chat
response = chain.invoke({"input": "My name is Alice"})
print(response['response'])

# Later... memory persists!
response = chain.invoke({"input": "What's my name?"})
print(response['response'])  # "Alice"
```

---

## Features

- 💾 **Persistent Memory** - Survives restarts
- 🔗 **LangChain Compatible** - Drop-in replacement
- 🚀 **Easy Setup** - 3 lines of code
- 🔒 **Session Isolation** - Multi-user support
- ✅ **Production Ready** - Tested and reliable

---

## API

### AlchemystMemory

```python
memory = AlchemystMemory(
    api_key="your-key",      # Alchemyst AI API key
    session_id="user-123"    # Unique session identifier
)
```

**Methods:**
- `save_context(inputs, outputs)` - Save conversation
- `load_memory_variables(inputs)` - Load history
- `clear()` - Clear session memory

---

## Examples

### Basic Usage

```python
memory = AlchemystMemory(
    api_key="your-key",
    session_id="session-1"
)

chain = ConversationChain(llm=llm, memory=memory)
chain.invoke({"input": "Hello!"})
```

### Multi-User Support

```python
# Different users, different sessions
alice_memory = AlchemystMemory(api_key=key, session_id="alice")
bob_memory = AlchemystMemory(api_key=key, session_id="bob")
```

### Clear Memory

```python
# Delete session data
memory.clear()
```

---

## Environment Setup

Create `.env` file:

```bash
ALCHEMYST_AI_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_key_here
```

---

## Development

```bash
# Install
pip install -e ".[dev]"

# Run tests
pytest

# Build
python -m build
```

---

## Get API Key

Sign up at [getalchemystai.com](https://getalchemystai.com)

---

## Links

- **Documentation**: https://getalchemystai.com/docs
- **GitHub**: https://github.com/Alchemyst-ai/alchemyst-langchain
- **PyPI**: https://pypi.org/project/alchemyst-langchain

---