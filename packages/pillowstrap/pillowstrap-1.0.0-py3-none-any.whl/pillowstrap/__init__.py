# pillowstrap/__init__.py

import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageOps
from .theme import THEME

class PillowStrap:
    def __init__(self, width=1200, height=800, bg="white"):
        self.width = width
        self.height = height
        bg_color = THEME['colors'].get(bg, bg)
        self.image = Image.new("RGBA", (width, height), bg_color)
        self.draw = ImageDraw.Draw(self.image)
        
        # Cursor tracks the Y position of rows
        self.cursor_y = 0 
        self.gutter = THEME['spacing']['gutter']

    def row(self, height):
        """ Creates a Row context manager. """
        return Row(self, height)

    def save(self, filename):
        self.image.save(filename)
        print(f"✅ Saved layout to {filename}")

class Row:
    def __init__(self, parent, height):
        self.parent = parent
        self.height = height
        self.cursor_x = 0 
        
        # Calculate available width (Total - Gutters)
        self.total_width = parent.width - (parent.gutter * 2)
        self.start_x = parent.gutter
        self.start_y = parent.cursor_y + parent.gutter

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Move the parent's cursor down past this row
        self.parent.cursor_y += self.height + self.parent.gutter

    def col(self, span=12, bg=None):
        """ 
        span: 1-12 (Grid size)
        bg: color name from theme
        """
        # 1. Calculate Column Width
        col_width = int((self.total_width / 12) * span)
        
        # 2. Define Box Coordinates (x1, y1, x2, y2)
        x1 = self.start_x + self.cursor_x
        y1 = self.start_y
        x2 = x1 + col_width
        y2 = y1 + self.height
        
        # Apply a small gap between columns
        gap = int(self.parent.gutter / 2)
        draw_box = [x1 + gap, y1, x2 - gap, y2]

        # 3. Draw Background
        if bg:
            c = THEME['colors'].get(bg, (200, 200, 200))
            self.parent.draw.rectangle(draw_box, fill=c)

        # 4. Advance X Cursor
        self.cursor_x += col_width
        
        return ColumnContext(self.parent.image, draw_box)

class ColumnContext:
    def __init__(self, image, box):
        self.image = image
        self.draw = ImageDraw.Draw(image)
        self.box = box # (x1, y1, x2, y2)
        self.width = box[2] - box[0]
        self.height = box[3] - box[1]
        
        # Vertical Stacking Cursors (Internal Padding)
        pad = THEME['spacing']['padding']
        self.cursor_x = box[0] + pad
        self.cursor_y = box[1] + pad
        self.max_w = self.width - (pad * 2)

    def text(self, content, size=30, color="dark", align="left", weight="regular"):
        """ Renders text with Auto-Wrap and Vertical Stacking """
        
        # A. Load Font
        font_name = THEME['fonts'].get(weight, "arial.ttf")
        try:
            font = ImageFont.truetype(font_name, size)
        except:
            font = ImageFont.load_default()

        # B. Word Wrap Logic
        avg_char_width = font.getlength("x")
        # Approximate chars per line
        chars_per_line = int(self.max_w / avg_char_width)
        wrapped_lines = textwrap.wrap(content, width=chars_per_line)

        # C. Draw Loop
        fill_color = THEME['colors'].get(color, (0,0,0))
        
        for line in wrapped_lines:
            # Alignment Math
            line_w = font.getlength(line)
            if align == "center":
                x = self.box[0] + (self.width - line_w) / 2
            elif align == "right":
                x = self.box[2] - line_w - THEME['spacing']['padding']
            else:
                x = self.cursor_x

            self.draw.text((x, self.cursor_y), line, font=font, fill=fill_color)
            
            # Stack Down
            bbox = font.getbbox(line)
            line_height = bbox[3] - bbox[1]
            self.cursor_y += line_height + 8 # Line spacing

        self.cursor_y += 15 # Paragraph spacing
        return self

    def img(self, path, fit="cover", padding=0):
        """ Places an external image inside the column """
        try:
            src = Image.open(path).convert("RGBA")
            
            # Target dimensions
            t_w = self.width - (padding * 2)
            t_h = self.height - (padding * 2)
            
            if fit == "cover":
                src = ImageOps.fit(src, (t_w, t_h), method=Image.Resampling.LANCZOS)
                px, py = self.box[0] + padding, self.box[1] + padding
            else: # contain
                src.thumbnail((t_w, t_h), Image.Resampling.LANCZOS)
                w, h = src.size
                # Center it
                px = self.box[0] + padding + (t_w - w) // 2
                py = self.box[1] + padding + (t_h - h) // 2

            self.image.paste(src, (int(px), int(py)), mask=src)
            
        except Exception as e:
            print(f"⚠️ Could not load image: {e}")
        
        return self