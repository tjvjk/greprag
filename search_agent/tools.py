TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "rg_search",
            "description": "Search for pattern in text files using ripgrep. By default searches all files in the docs folder. You can optionally specify a file_path to search a specific file or subfolder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for",
                    },
                    "ignore_case": {
                        "type": "boolean",
                        "default": True,
                        "description": "Case insensitive search",
                    },
                    "context_lines": {
                        "type": "integer",
                        "default": 2,
                        "description": "Number of context lines to show around matches",
                    },
                    "fixed_string": {
                        "type": "boolean",
                        "default": False,
                        "description": "Treat pattern as fixed string, not regex",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Optional: specific file or folder to search. If not provided, searches the entire docs folder. Use this when you want to search within a specific file found from previous searches.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_lines",
            "description": "Read specific line range from a file. Use this after finding relevant content with rg_search to get more context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_line": {
                        "type": "integer",
                        "description": "Starting line number to read",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Ending line number to read",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Full path to the file to read from. Extract this from rg_search results (the part before the colon and line number).",
                    },
                },
                "required": ["start_line", "end_line", "file_path"],
            },
        },
    },
]
