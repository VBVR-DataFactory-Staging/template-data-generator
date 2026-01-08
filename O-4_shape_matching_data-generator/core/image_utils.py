"""Image utilities."""

from PIL import Image, ImageDraw
from typing import Tuple


class ImageRenderer:
    """Helper for image rendering."""
    
    def __init__(self, image_size: Tuple[int, int] = (400, 400)):
        self.image_size = image_size
    
    def create_blank_image(self, bg_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
        """Create blank RGB image."""
        return Image.new('RGB', self.image_size, bg_color)
    
    def draw_grid(self, image: Image.Image, rows: int, cols: int) -> Image.Image:
        """Draw grid on image."""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        cell_w, cell_h = width / cols, height / rows
        
        for i in range(cols + 1):
            x = int(i * cell_w)
            draw.line([(x, 0), (x, height)], fill=(200, 200, 200), width=2)
        for i in range(rows + 1):
            y = int(i * cell_h)
            draw.line([(0, y), (width, y)], fill=(200, 200, 200), width=2)
        return image
    
    def draw_text(self, image: Image.Image, text: str, position: Tuple[int, int]) -> Image.Image:
        """Draw text on image."""
        draw = ImageDraw.Draw(image)
        draw.text(position, text, fill=(0, 0, 0))
        return image
    
    @staticmethod
    def ensure_rgb(image: Image.Image) -> Image.Image:
        """Convert image to RGB."""
        return image.convert('RGB') if image.mode != 'RGB' else image
