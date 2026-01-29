# thinkpdf

Extract text, tables, and structure from PDFs. Built for RAG pipelines, AI training, and LLM context.

Read directly into memory or save as Markdown. Supports OCR.

## Install

[![Get it from the Snap Store](https://snapcraft.io/en/dark/install.svg)](https://snapcraft.io/thinkpdf)

```bash
pip install thinkpdf        # Python (PyPI)
npx thinkpdf                 # npm (run directly)
brew install thinkpdf        # macOS (Homebrew)
choco install thinkpdf       # Windows (Chocolatey)
snap install thinkpdf        # Linux (Snap Store)
conda install -c conda-forge thinkpdf  # Anaconda (pending)
```

For better table extraction (but slower):
```bash
pip install thinkpdf[docling]
```

## Quick Start

```bash
thinkpdf document.pdf                # outputs document.md
thinkpdf document.pdf -o output.md   # custom output
thinkpdf folder/ --batch             # convert all PDFs
```

```python
from thinkpdf import convert
convert("document.pdf")  # returns markdown
```

## GUI

```bash
pip install thinkpdf[gui]
thinkpdf-gui
```

## MCP Server

Add to your MCP config:

```json
{
  "mcpServers": {
    "thinkpdf": {
      "command": "python",
      "args": ["-m", "thinkpdf.mcp_server"]
    }
  }
}
```

| Tool | Description |
|------|-------------|
| `read_pdf` | Read PDF content into context |
| `convert_pdf` | Convert and save to file |
| `get_document_info` | Get PDF metadata |

## License

AGPL-3.0
