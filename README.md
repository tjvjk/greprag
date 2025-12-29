# GrepRAG - Multi-File Search Agent

An AI-powered search agent that uses RAG (Retrieval-Augmented Generation) to search and synthesize information from multiple markdown files. The agent uses ripgrep (rg) and sed for fast, efficient searching across large document collections.

## Features

- **Multi-file search**: Search across 2,139+ markdown files simultaneously
- **Intelligent synthesis**: Uses LLM to analyze and combine information from multiple sources
- **Fast search tools**: Leverages ripgrep for high-performance text searching
- **Interactive CLI**: User-friendly command-line interface
- **Structured responses**: Returns answers with citations and source references
- **Cost tracking**: Monitors token usage and API costs

## Architecture

The agent uses:
- **OpenAI-compatible API** via OpenRouter (currently using Grok 4.1 Fast)
- **Function calling** with custom tools (rg_search, read_lines)
- **Async Python** for efficient I/O operations
- **Pydantic models** for structured responses
- **Comprehensive logging** to console and file

## Installation

1. Clone the repository
2. Install dependencies:
```bash
uv sync
```

3. Set up environment variables in `.env`:
```bash
OPENROUTER_API_KEY=your_api_key_here
```

4. Make sure you have ripgrep installed:
```bash
# macOS
brew install ripgrep

# Ubuntu/Debian
sudo apt-get install ripgrep

# Windows
choco install ripgrep
```

## Usage

Run a single query and exit:

```bash
python search_agent/agent.py "Your search query here"
```

**Example:**
```bash
python search_agent/agent.py "методы педагогики"
```

This mode outputs full JSON response and is useful for scripting or automation.

## Project Structure

```
greprag/
├── search_agent/
│   ├── __init__.py
│   ├── agent.py          # Main agent logic and CLI interface
│   ├── tools.py          # Tool definitions for function calling
│   ├── models.py         # Pydantic response models
│   └── prompts.py        # System prompt with search strategy
├── docs/                 # Document collection (2,139+ markdown files)
├── logs/                 # Application logs
│   └── bot.log
├── settings.py           # Configuration and environment variables
├── .env                  # Environment variables (not in git)
├── pyproject.toml        # Project dependencies
└── README.md            # This file
```

## How It Works

1. **Query Analysis**: The agent analyzes your query and generates comprehensive search terms
2. **Multi-file Search**: Uses ripgrep to search across all files in parallel
3. **Context Extraction**: Uses sed to read specific line ranges from relevant files
4. **Synthesis**: LLM combines information from multiple sources
5. **Structured Output**: Returns answer with citations and metadata

### Search Strategy

The agent follows an exhaustive search strategy:

- Generates multiple search patterns (grammatical forms, synonyms, word stems)
- Runs 3-5 different search patterns per concept
- Searches across ALL files by default
- Can focus on specific files when needed
- Groups findings by themes and perspectives

### Available Tools

**rg_search** - Search for patterns using ripgrep
- Parameters: `pattern`, `ignore_case`, `context_lines`, `fixed_string`, `file_path`
- Returns: Matching lines with file paths and line numbers
- Default: Searches entire docs folder

**read_lines** - Read specific line ranges from files
- Parameters: `start_line`, `end_line`, `file_path`
- Returns: Content from specified line range
- Used to get more context around search matches

## Configuration

Edit `settings.py` to configure:

```python
# Model configuration
MODEL = "x-ai/grok-4.1-fast"  # OpenRouter model
INPUT_PRICE = 0.2              # Price per 1M input tokens
OUTPUT_PRICE = 0.5             # Price per 1M output tokens

# Search configuration
DOCS_FOLDER = "docs"           # Folder containing markdown files

# Logging
LOG_LEVEL = logging.INFO
LOG_FILE = "logs/bot.log"
```

## Response Format

The agent returns structured responses with:

```json
{
  "question": "Original query",
  "answer": "Synthesized answer from multiple sources",
  "citations": [
    {
      "location": "filename.md",
      "text": "Relevant quote or passage"
    }
  ]
}
```

## Testing

Run the test script to verify functionality:

```bash
python test_agent.py
```

This will run a sample query and display the full response with statistics.

## Logging

All activity is logged to:
- **Console**: Real-time output
- **File**: `logs/bot.log` (rotating, max 10MB, 5 backups)

## Requirements

- Python 3.13+
- ripgrep (rg)
- sed
- OpenRouter API key

## Dependencies

Main dependencies:
- `openai` - For OpenAI-compatible API access
- `pydantic` - For data validation and structured responses
- `python-dotenv` - For environment variable management
- `asyncio` - For async operations

See `pyproject.toml` for complete list.

## Performance

- **Search speed**: Ripgrep searches 2,139 files in milliseconds
- **Token efficiency**: Smart context extraction minimizes token usage
- **Cost tracking**: Real-time monitoring of API costs
- **Async I/O**: Non-blocking operations for better performance

## Tips

1. **Use Russian queries** for better results (corpus is in Russian)
2. **Be specific** - detailed queries get better synthesized answers
3. **Check citations** - verify information in source files
4. **Monitor costs** - watch token usage in statistics output
5. **Use interactive mode** for exploratory research

## Troubleshooting

**No matches found:**
- Try broader search terms
- Check spelling and grammar
- Use word stems (e.g., "мотивац" instead of "мотивация")

**High costs:**
- Reduce `context_lines` in searches
- Use more specific queries
- Monitor token usage in statistics

**Slow responses:**
- Check internet connection
- Verify OpenRouter API status
- Reduce number of search patterns

## License

[Your license here]

## Contributing

[Your contribution guidelines here]
