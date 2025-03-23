# Model

## Overview

This model uses a combination of vector search, reranking, and large language models to answer questions about Northeastern University using institutional knowledge,previously scrapped and stored .

## Features

- Vector-based semantic search using Pinecone
- Document reranking with Cohere
- LLM-powered conversational responses via OpenAI
- Custom embedding model integration (Snowflake Arctic)

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install requirements.txt
   ```
3. Set up your configuration in `config.py`

## Usage

```python
python model.py
```

## Configuration

The system is fully configurable through the `config.py` file:

- Vector database settings (Pinecone)
- Embedding model selection
- LLM parameters and provider options
- Retrieval and reranking settings
- Conversational prompt templates
