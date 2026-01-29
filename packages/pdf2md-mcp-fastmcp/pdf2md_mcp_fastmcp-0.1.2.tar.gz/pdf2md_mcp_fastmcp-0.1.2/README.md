[![Add to Cursor](https://fastmcp.me/badges/cursor_dark.svg)](https://fastmcp.me/MCP/Details/1700/pdf2md)
[![Add to VS Code](https://fastmcp.me/badges/vscode_dark.svg)](https://fastmcp.me/MCP/Details/1700/pdf2md)
[![Add to Claude](https://fastmcp.me/badges/claude_dark.svg)](https://fastmcp.me/MCP/Details/1700/pdf2md)
[![Add to ChatGPT](https://fastmcp.me/badges/chatgpt_dark.svg)](https://fastmcp.me/MCP/Details/1700/pdf2md)
[![Add to Codex](https://fastmcp.me/badges/codex_dark.svg)](https://fastmcp.me/MCP/Details/1700/pdf2md)
[![Add to Gemini](https://fastmcp.me/badges/gemini_dark.svg)](https://fastmcp.me/MCP/Details/1700/pdf2md)

# PDF2MD MCP Server

An MCP (Model Context Protocol) server that converts PDF files to Markdown format using AI sampling capabilities.

## Features

- Convert PDF files to Markdown using AI content extraction
- Support for both local file paths and URLs
- Incremental conversion - resume from where you left off
- Configurable output directory
- Built with FastMCP for high performance

## Installation

```bash
pip install pdf2md-mcp
```

## Usage

### As an MCP Server

Start the server:

```bash
pdf2md-mcp
```

The server will expose MCP tools for PDF to Markdown conversion.

### Available Tools

#### `convert_pdf_to_markdown`

Converts a PDF file to Markdown format using AI sampling.

**Parameters:**
- `file_path` (string): Local file path or URL to the PDF file
- `output_dir` (string, optional): Output directory for the markdown file. Defaults to the same directory as input file (for local files) or current working directory (for URLs)

**Returns:**
- `output_file`: Path to the generated markdown file
- `summary`: Summary of the conversion task
- `pages_processed`: Number of pages processed

## Requirements

- Python 3.10+
- An MCP-compatible client with AI sampling capabilities
- Network access for URL-based PDF files

## Development

### Setup

```bash
git clone https://github.com/shuminghuang/pdf2md-mcp.git
cd pdf2md-mcp
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
