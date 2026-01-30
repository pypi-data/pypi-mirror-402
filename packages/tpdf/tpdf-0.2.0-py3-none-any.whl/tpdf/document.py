"""TPDF document creation API"""

import json


class TPDF:
    """Easy API for creating TPDF documents"""
    
    def __init__(self, width=612, height=792, background='#ffffff', multipage=False):
        """
        Create a new TPDF document
        
        Args:
            width: Page width in points (default: 612 = 8.5")
            height: Page height in points (default: 792 = 11")
            background: Hex color for background
            multipage: If True, creates multi-page document
        """
        self.multipage = multipage
        self.default_width = width
        self.default_height = height
        self.default_background = background
        
        if multipage:
            self.data = {
                'version': '1.0',
                'pages': []
            }
            self.current_page = None
        else:
            self.data = {
                'version': '1.0',
                'page': {
                    'width': width,
                    'height': height,
                    'background': background
                },
                'elements': []
            }
    
    def add_page(self, width=None, height=None, background=None):
        """
        Add a new page (only for multipage documents)
        
        Args:
            width: Page width (uses default if None)
            height: Page height (uses default if None)
            background: Page background (uses default if None)
        
        Returns:
            self (for chaining)
        """
        if not self.multipage:
            raise ValueError(
                "add_page() only works for multipage documents. "
                "Set multipage=True in constructor."
            )
        
        page = {
            'width': width or self.default_width,
            'height': height or self.default_height,
            'background': background or self.default_background,
            'elements': []
        }
        self.data['pages'].append(page)
        self.current_page = page
        return self
    
    def add_text(self, content, x=None, y=None, **options):
        """
        Add text to the document
        
        Args:
            content: Text content
            x: X coordinate in points (None for alignment-based positioning)
            y: Y coordinate in points (from top)
            **options: 
                fontSize: Font size (default: 12)
                fontFamily: 'Helvetica', 'Times', 'Courier' (default: 'Helvetica')
                color: Hex color (default: '#000000')
                fontWeight: 'normal' or 'bold' (default: 'normal')
                fontStyle: 'normal' or 'italic' (default: 'normal')
                align: 'left', 'center', 'right' (default: 'left')
                valign: 'top', 'middle', 'bottom' (for vertical alignment)
                maxWidth: Maximum width before wrapping (default: None)
                lineHeight: Line height multiplier (default: 1.2)
        
        Returns:
            self (for chaining)
        """
        element = {
            'type': 'text',
            'content': str(content),
            'x': float(x) if x is not None else None,
            'y': float(y) if y is not None else None,
            'fontSize': options.get('fontSize', 12),
            'fontFamily': options.get('fontFamily', 'Helvetica'),
            'color': options.get('color', '#000000'),
            'fontWeight': options.get('fontWeight', 'normal'),
            'fontStyle': options.get('fontStyle', 'normal'),
            'align': options.get('align', 'left'),
            'valign': options.get('valign', None),
            'maxWidth': options.get('maxWidth', None),
            'lineHeight': options.get('lineHeight', 1.2)
        }
        
        if self.multipage:
            if self.current_page is None:
                raise ValueError(
                    "Must call add_page() before adding elements "
                    "to multipage document"
                )
            self.current_page['elements'].append(element)
        else:
            self.data['elements'].append(element)
        
        return self
    
    def add_paragraph(self, content, x, y, maxWidth, **options):
        """
        Add a paragraph with automatic text wrapping
        
        Args:
            content: Paragraph text
            x: X coordinate
            y: Y coordinate (top of paragraph)
            maxWidth: Maximum width for wrapping
            **options: Same as add_text
        
        Returns:
            self (for chaining)
        """
        options['maxWidth'] = maxWidth
        return self.add_text(content, x, y, **options)
    
    def center(self, content, y, **options):
        """
        Add centered text (horizontal)
        
        Args:
            content: Text content
            y: Y coordinate
            **options: Same as add_text
        
        Returns:
            self (for chaining)
        """
        options['align'] = 'center'
        return self.add_text(content, None, y, **options)
    
    def left(self, content, y, margin=50, **options):
        """
        Add left-aligned text
        
        Args:
            content: Text content
            y: Y coordinate
            margin: Left margin (default: 50)
            **options: Same as add_text
        
        Returns:
            self (for chaining)
        """
        options['align'] = 'left'
        return self.add_text(content, margin, y, **options)
    
    def right(self, content, y, margin=50, **options):
        """
        Add right-aligned text
        
        Args:
            content: Text content
            y: Y coordinate
            margin: Right margin (default: 50)
            **options: Same as add_text
        
        Returns:
            self (for chaining)
        """
        options['align'] = 'right'
        return self.add_text(content, None, y, **options)
    
    def vcenter(self, content, x=None, **options):
        """
        Add vertically centered text
        
        Args:
            content: Text content
            x: X coordinate (None for horizontal center too)
            **options: Same as add_text
        
        Returns:
            self (for chaining)
        """
        options['valign'] = 'middle'
        if x is None:
            options['align'] = 'center'
        return self.add_text(content, x, None, **options)
    
    def add_image(self, url, x, y, width, height, **options):
        """
        Add image to the document
        
        Args:
            url: Image URL
            x: X coordinate in points (None for alignment)
            y: Y coordinate in points (from top)
            width: Image width in points
            height: Image height in points
            **options: align ('left', 'center', 'right')
        
        Returns:
            self (for chaining)
        """
        element = {
            'type': 'image',
            'url': str(url),
            'x': float(x) if x is not None else None,
            'y': float(y) if y is not None else None,
            'width': float(width),
            'height': float(height),
            'align': options.get('align', 'left')
        }
        
        if self.multipage:
            if self.current_page is None:
                raise ValueError(
                    "Must call add_page() before adding elements "
                    "to multipage document"
                )
            self.current_page['elements'].append(element)
        else:
            self.data['elements'].append(element)
        
        return self
    
    def set_background(self, color):
        """Set page background color"""
        if self.multipage:
            if self.current_page is None:
                raise ValueError(
                    "Must call add_page() before setting background"
                )
            self.current_page['background'] = color
        else:
            self.data['page']['background'] = color
        return self
    
    def to_json(self):
        """Export as JSON string"""
        return json.dumps(self.data, indent=2)
    
    def save_tpdf(self, filename):
        """Save as .tpdf file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        return self
    
    def compile_to_pdf(self, filename):
        """Compile directly to PDF"""
        from .compiler import TPDFCompiler
        compiler = TPDFCompiler(self.data)
        compiler.compile(filename)
        return self
