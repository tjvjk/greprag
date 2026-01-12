# GrepRAG

An AI-powered search agent that uses RAG (Retrieval-Augmented Generation) to search and synthesize information from multiple markdown files using ripgrep.

## Installation

```bash
uv sync
```

Requires ripgrep (`brew install ripgrep` on macOS).

## Configuration

Create a `.env` file:

```bash
OPENROUTER_API_KEY=your_api_key_here
```

## Usage

```bash
python search_agent/agent.py "Your search query here"
```

Returns a JSON response with the answer and citations to source files.