TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search for pattern in text files and PDFs using ugrep. By default searches all files in the docs folder. You can optionally specify a path to search a specific file or subfolder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for",
                    },
                    "path": {
                        "type": "string",
                        "description": "Optional: specific file or folder to search. If not provided, searches the entire docs folder.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_folder",
            "description": "List all files in a topic folder. Returns FULL FILE PATHS that can be used directly with search(path=...). Use after finding relevant results to discover sibling files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder": {
                        "type": "string",
                        "description": "Topic folder name (e.g., 'pole_flip' or 'solid_inner_core')",
                    },
                },
                "required": ["folder"],
            },
        },
    },
]
