# TPDF - Text Portable Document Format

AI-friendly PDF generation library with a simple JSON-based format.

## Features

- 🤖 **AI-Friendly**: Simple JSON format perfect for LLMs to generate
- 📄 **Multi-Page Support**: Create documents with unlimited pages
- 🎨 **Styling**: Custom fonts, colors, sizes, and weights
- 🖼️ **Images**: Embed images from URLs
- 🎯 **Precise Positioning**: X/Y coordinates for exact layout control
- 🔄 **Two-Way Conversion**: JSON ↔ PDF

## Installation

```bash
pip install tpdf
```

## Quick Start

### Single Page Document

```python
from tpdf import TPDF

# Create document
doc = TPDF()

# Add content
doc.add_text('Hello, World!', 100, 100, fontSize=24, fontWeight='bold')
doc.add_text('This is TPDF', 100, 150, fontSize=14, color='#666666')
doc.add_image('https://example.com/logo.png', 100, 200, 200, 100)

# Generate PDF
doc.compile_to_pdf('output.pdf')
```

### Multi-Page Document

```python
from tpdf import TPDF

# Create multi-page document
doc = TPDF(multipage=True)

# Page 1
doc.add_page(background='#f0f9ff')
doc.add_text('Cover Page', 306, 400, fontSize=48, fontWeight='bold')

# Page 2
doc.add_page()
doc.add_text('Introduction', 50, 60, fontSize=24)
doc.add_text('Lorem ipsum...', 50, 100, fontSize=12)

# Generate PDF
doc.compile_to_pdf('document.pdf')
```

### Save as TPDF Format

```python
# Save as .tpdf (JSON) for later use
doc.save_tpdf('document.tpdf')

# Load and compile later
from tpdf import TPDFCompiler
import json

with open('document.tpdf', 'r') as f:
    data = json.load(f)

compiler = TPDFCompiler(data)
compiler.compile('output.pdf')
```

## API Reference

### TPDF Class

#### `__init__(width=612, height=792, background='#ffffff', multipage=False)`
Create a new TPDF document.

**Parameters:**
- `width`: Page width in points (default: 612 = 8.5")
- `height`: Page height in points (default: 792 = 11")
- `background`: Hex color for background
- `multipage`: Enable multi-page mode

#### `add_text(content, x, y, **options)`
Add text element.

**Parameters:**
- `content`: Text string
- `x`: X coordinate (from left)
- `y`: Y coordinate (from top)
- `fontSize`: Font size in points (default: 12)
- `fontFamily`: 'Helvetica', 'Times', 'Courier' (default: 'Helvetica')
- `color`: Hex color (default: '#000000')
- `fontWeight`: 'normal' or 'bold' (default: 'normal')
- `fontStyle`: 'normal' or 'italic' (default: 'normal')

#### `add_image(url, x, y, width, height)`
Add image element.

**Parameters:**
- `url`: Image URL
- `x`: X coordinate
- `y`: Y coordinate
- `width`: Image width in points
- `height`: Image height in points

#### `add_page(width=None, height=None, background=None)`
Add new page (multipage mode only).

#### `compile_to_pdf(filename)`
Generate PDF file.

#### `save_tpdf(filename)`
Save as .tpdf JSON file.

## TPDF Format Specification

### Single Page Format
```json
{
  "version": "1.0",
  "page": {
    "width": 612,
    "height": 792,
    "background": "#ffffff"
  },
  "elements": [
    {
      "type": "text",
      "content": "Hello",
      "x": 100,
      "y": 100,
      "fontSize": 12,
      "fontFamily": "Helvetica",
      "color": "#000000",
      "fontWeight": "normal",
      "fontStyle": "normal"
    },
    {
      "type": "image",
      "url": "https://example.com/image.png",
      "x": 100,
      "y": 200,
      "width": 200,
      "height": 150
    }
  ]
}
```

### Multi-Page Format
```json
{
  "version": "1.0",
  "pages": [
    {
      "width": 612,
      "height": 792,
      "background": "#ffffff",
      "elements": [...]
    },
    {
      "width": 612,
      "height": 792,
      "background": "#f0f0f0",
      "elements": [...]
    }
  ]
}
```

## Use Cases

- 🤖 **AI-Generated Reports**: LLMs can easily generate TPDF JSON
- 📊 **Dynamic Documents**: Programmatically create PDFs from data
- 📄 **Document Templates**: Store layouts as JSON
- 🔄 **Document Pipeline**: Convert JSON → PDF in workflows

## Examples

See the [examples](https://github.com/thecoolrobot/tpdf/tree/main/examples) directory for more use cases:
- Invoice generation
- Certificate creation
- Report templates
- Multi-page proposals

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please open an issue or submit a PR.

## Credits

Built with [ReportLab](https://www.reportlab.com/) for reliable PDF generation.