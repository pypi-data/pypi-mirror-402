# Markdown Live Server (mdv)

A local markdown server with live reload using Pandoc. Changes are detected automatically!

## Features

- Live reload when files change
- Table of contents generation
- Dark mode support
- Code syntax highlighting
- Graphviz diagram rendering
- PlantUML diagram rendering

## Installation

```bash
pipx install markdown-live-server
```

### Requirements

- **pandoc** (required) - Markdown/RST to HTML converter
- **graphviz** (optional) - For rendering `dot` diagrams
- **plantuml** (optional) - For rendering PlantUML diagrams

## Usage

### CLI Mode (terminal output)

```bash
mdv file.md
```

### Server Mode (web browser)

```bash
mdv                    # Start server in current directory
mdv /path/to/docs      # Start server in specific directory
mdv -a -b              # Auto-refresh + open browser
```

### Options

- `-a` Enable auto-refresh (live reload)
- `-b` Open browser automatically
- `-r` Allow remote connections (bind to all interfaces)
- `-p PORT` Port number (default: 8080)

## Attribution

Based on [Panserver](http://pandoc.org/) by [Marcel Fischer](http://marcelfischer.eu/).

## License

MIT
