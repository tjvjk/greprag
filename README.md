# GrepRAG

An AI-powered search agent that uses RAG (Retrieval-Augmented Generation) to search and synthesize information from PDFs and text files using ugrep.

## Installation

```bash
uv sync
```

Requires ugrep and pdftotext:

```bash
brew install ugrep poppler
```

## Documents

Place your PDFs and text files in the `docs/` folder, or configure `DOCS_FOLDER` in `settings.py` to point to an existing folder.

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

## Example

```bash
python search_agent/agent.py "What are the top technology trends for 2026?"
```

```json
{
  "question": "What are the top technology trends for 2026?",
  "answer": "The top technology trends for 2026 include AI-powered automation, quantum computing advancements, and sustainable tech solutions.",
  "citations": [
    {
      "location": "tech-trends-2026.pdf",
      "text": "AI-powered automation continues to dominate enterprise adoption..."
    }
    ...
  ]
}
```
