# Reindexer Vector Store for LangChain

This package provides a vector store integration for [Reindexer](https://reindexer.io/) database with the [LangChain](https://github.com/hwchase17/langchain) framework.

## Installation

```bash
pip install langchain-reindexer
```

## Usage
Now you can use the vector store in your LangChain application:

```python
from langchain_reindexer import ReindexerVectorStore
from langchain_openai import OpenAIEmbeddings

# Initialize the vector store
vector_store = ReindexerVectorStore(
    embedding=OpenAIEmbeddings(),
    rx_connector_config={"dsn": "builtin:///tmp/my_db"},
    rx_namespace="my_namespace",
)

# Add documents
from langchain_core.documents import Document

documents = [
    Document(page_content="foo", metadata={"baz": "bar"}),
    Document(page_content="thud", metadata={"bar": "baz"}),
]

ids = vector_store.add_documents(documents=documents)

# Search
results = vector_store.similarity_search(query="thud", k=1)
```
More examples [here](https://github.com/Restream/langchain-reindexer/blob/main/examples/reindexer_en.ipynb)
## Features

- Add and delete documents
- Similarity search with and without scores
- Metadata filtering
- Maximal Marginal Relevance (MMR) search
- Async support
- Save and load vector store configuration
