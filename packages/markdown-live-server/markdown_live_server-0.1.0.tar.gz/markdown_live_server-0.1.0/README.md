# Markdown Live Server (mdv)

A local markdown server with live reload using Pandoc. Changes are detected automatically!

## Features

- Live reload when files change
- Table of contents generation
- Dark mode support
- Code syntax highlighting
- Graphviz diagram rendering
- PlantUML diagram rendering

## Requirements

**Python packages (pip install):**
- bottle - Web framework

**External programs (system install):**
- pandoc - REQUIRED: Markdown/RST to HTML converter
- graphviz - OPTIONAL: For rendering 'dot' diagrams
- plantuml - OPTIONAL: For rendering PlantUML diagrams

### Termux installation

```bash
pkg install pandoc graphviz
pip install bottle
```

## Usage

### CLI Mode (terminal output)

```bash
./mdv.sh file.md
```

### Server Mode (web browser)

```bash
./mdv.sh
```

Or with options:

```bash
python panserver.py [path] [-p PORT] [-a] [-b] [-r]
```

- `-a` Enable auto-refresh (live reload)
- `-b` Open browser automatically
- `-r` Allow remote connections (bind to all interfaces)
- `-p` Port number (default: 8080)

## Attribution

Based on [Panserver](http://pandoc.org/) by [Marcel Fischer](http://marcelfischer.eu/).

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
