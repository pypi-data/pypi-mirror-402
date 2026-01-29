"""TPDF to PDF compilation"""

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import requests
import json
from io import BytesIO


class TPDFCompiler:
    """Compiles TPDF JSON format into actual PDF files"""
    
    def __init__(self, tpdf_data):
        """
        Initialize with TPDF data (dict or JSON string)
        
        Args:
            tpdf_data: TPDF data as dict or JSON string
        """
        if isinstance(tpdf_data, str):
            self.data = json.loads(tpdf_data)
        else:
            self.data = tpdf_data
    
    def compile(self, output_filename):
        """
        Compile TPDF to PDF file
        
        Args:
            output_filename: Path to save the PDF
        """
        # Check if multi-page format
        if 'pages' in self.data:
            self._compile_multipage(output_filename)
        else:
            self._compile_single_page(output_filename)
    
    def _compile_single_page(self, output_filename):
        """Compile single page document"""
        page = self.data.get('page', {})
        width = page.get('width', 612)
        height = page.get('height', 792)
        
        # Create PDF canvas
        c = canvas.Canvas(output_filename, pagesize=(width, height))
        
        # Set background
        background = page.get('background', '#ffffff')
        if background and background != '#ffffff':
            c.setFillColor(HexColor(background))
            c.rect(0, 0, width, height, fill=1, stroke=0)
        
        # Process elements
        for element in self.data.get('elements', []):
            if element['type'] == 'text':
                self._add_text(c, element, height)
            elif element['type'] == 'image':
                self._add_image(c, element, height)
        
        c.save()
        print(f"✅ PDF generated: {output_filename}")
    
    def _compile_multipage(self, output_filename):
        """Compile multi-page document"""
        pages = self.data.get('pages', [])
        if not pages:
            raise ValueError("No pages found in TPDF document")
        
        # Get default page size from first page
        first_page = pages[0]
        width = first_page.get('width', 612)
        height = first_page.get('height', 792)
        
        # Create PDF canvas
        c = canvas.Canvas(output_filename, pagesize=(width, height))
        
        # Process each page
        for page_num, page in enumerate(pages):
            page_width = page.get('width', width)
            page_height = page.get('height', height)
            
            # Set background
            background = page.get('background', '#ffffff')
            if background and background != '#ffffff':
                c.setFillColor(HexColor(background))
                c.rect(0, 0, page_width, page_height, fill=1, stroke=0)
            
            # Process elements on this page
            for element in page.get('elements', []):
                if element['type'] == 'text':
                    self._add_text(c, element, page_height)
                elif element['type'] == 'image':
                    self._add_image(c, element, page_height)
            
            # Add new page if not last page
            if page_num < len(pages) - 1:
                c.showPage()
        
        c.save()
        print(f"✅ PDF generated: {output_filename} ({len(pages)} pages)")
    
    def _add_text(self, c, element, page_height):
        """Add text element to PDF"""
        # Convert Y coordinate (PDF origin is bottom-left)
        y = page_height - element['y']
        
        # Set font
        font_family = element.get('fontFamily', 'Helvetica')
        font_size = element.get('fontSize', 12)
        font_weight = element.get('fontWeight', 'normal')
        font_style = element.get('fontStyle', 'normal')
        
        # Map font to ReportLab font names
        font_name = self._get_font_name(font_family, font_weight, font_style)
        c.setFont(font_name, font_size)
        
        # Set color
        color = element.get('color', '#000000')
        c.setFillColor(HexColor(color))
        
        # Draw text
        c.drawString(element['x'], y, element['content'])
    
    def _add_image(self, c, element, page_height):
        """Add image element to PDF"""
        try:
            # Convert Y coordinate
            y = page_height - element['y'] - element['height']
            
            # Fetch image
            response = requests.get(element['url'], timeout=10)
            response.raise_for_status()
            img = ImageReader(BytesIO(response.content))
            
            # Draw image
            c.drawImage(
                img,
                element['x'],
                y,
                width=element['width'],
                height=element['height'],
                preserveAspectRatio=True
            )
        except Exception as e:
            print(f"⚠️  Warning: Could not load image {element['url']}: {e}")
    
    def _get_font_name(self, family, weight, style):
        """Map font properties to ReportLab font names"""
        # ReportLab built-in fonts
        family_lower = family.lower()
        
        if 'helvetica' in family_lower or 'arial' in family_lower:
            if weight == 'bold' and style == 'italic':
                return 'Helvetica-BoldOblique'
            elif weight == 'bold':
                return 'Helvetica-Bold'
            elif style == 'italic':
                return 'Helvetica-Oblique'
            return 'Helvetica'
        
        elif 'times' in family_lower:
            if weight == 'bold' and style == 'italic':
                return 'Times-BoldItalic'
            elif weight == 'bold':
                return 'Times-Bold'
            elif style == 'italic':
                return 'Times-Italic'
            return 'Times-Roman'
        
        elif 'courier' in family_lower:
            if weight == 'bold' and style == 'italic':
                return 'Courier-BoldOblique'
            elif weight == 'bold':
                return 'Courier-Bold'
            elif style == 'italic':
                return 'Courier-Oblique'
            return 'Courier'
        
        # Default to Helvetica
        return 'Helvetica'