# image_processor.py

import logging
import os
from PIL import Image
import rembg
from io import BytesIO

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        try:
            self.rembg_session = rembg.new_session('u2net')
        except Exception as e:
            logger.warning(f"Could not initialize u2net model, using default: {e}")
            self.rembg_session = None
    
    def validate_image(self, image_path):
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False
    
    def remove_background(self, image_path):
        try:
            with open(image_path, 'rb') as input_file:
                input_data = input_file.read()
            
            if self.rembg_session:
                output_data = rembg.remove(input_data, session=self.rembg_session)
            else:
                output_data = rembg.remove(input_data)
            
            return Image.open(BytesIO(output_data))
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            return None
            
    def resize_image_to_fit(self, image, max_width, max_height, maintain_aspect=True):
        if maintain_aspect:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            return image
        else:
            return image.resize((max_width, max_height), Image.Resampling.LANCZOS)

    def process_image_with_dimensions(self, product_path, template_data: bytes, user_id, target_width, target_height, image_index=1):
        try:
            logger.info(f"Processing image for user {user_id} with dimensions {target_width}x{target_height}")
            
            product_no_bg = self.remove_background(product_path)
            if product_no_bg is None:
                return None

            product_resized = self.resize_image_to_fit(product_no_bg, target_width, target_height, maintain_aspect=True)

            # Open template from bytes data
            template = Image.open(BytesIO(template_data)).convert('RGBA')

            # Center the product on the template
            x = (template.width - product_resized.width) // 2
            y = (template.height - product_resized.height) // 2
            
            result = template.copy()
            result.paste(product_resized, (x, y), product_resized)
            
            # Convert to RGB for saving as JPEG
            background = Image.new('RGB', result.size, (255, 255, 255))
            background.paste(result, mask=result.split()[-1])
            result = background

            output_path = f"temp/result_{user_id}_{image_index}.jpg"
            result.save(output_path, 'JPEG', quality=95)
            
            logger.info(f"Image processing completed for user {user_id}")
            return output_path
            
        except Exception as e:
            logger.error(f"Image processing with dimensions failed: {e}")
            return None
