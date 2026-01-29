# markmap-export

Export [Markmap](https://markmap.js.org/) mind maps to high-resolution PNG.

## Install

```bash
uv tool install markmap-export
markmap-export --install-browser
```

## CLI

```bash
markmap-export mindmap.html
markmap-export mindmap.html -o output.png -s 2
```

## Library

```python
from markmap_export import export_png, export_bytes

export_png("mindmap.html")
png_data = export_bytes("mindmap.html", scale=2)
```

## License

MIT
