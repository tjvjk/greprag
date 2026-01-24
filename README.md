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

Copy `.env.example` to `.env` and add your API key:

```bash
cp .env.example .env
```

The default model is `x-ai/grok-4.1-fast`. Change `MODEL` in `settings.py` to use a different model from OpenRouter.

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

## Benchmark

Evaluate search quality using the [BRIGHT](https://github.com/xlang-ai/BRIGHT) benchmark with Recall@K metric.

### GrepRAG Benchmark

Install benchmark dependencies:

```bash
uv sync --extra benchmark
```

Run benchmark:

```bash
uv run python -m benchmark.grep --split biology --limit 5
```

Save results to file:

```bash
uv run python -m benchmark.grep --split biology --output "results/$(date +%Y%m%d%H%M)_grep_biology.json"
```

### Vector Store Benchmark

Compare GrepRAG against a traditional vector store using semantic embeddings.

Run benchmark:

```bash
uv run python -m benchmark.vector --split biology --limit 5
```

Save results to file:

```bash
uv run python -m benchmark.vector --split biology --output "results/$(date +%Y%m%d%H%M)_vector_biology.json"
```

### Available Splits

`biology`, `earth_science`, `economics`, `psychology`, `robotics`, `stackoverflow`, `sustainable_living`, `leetcode`, `pony`, `aops`, `theoremqa_theorems`, `theoremqa_questions`.
