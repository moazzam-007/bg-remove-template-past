# config.py

import os

class Config:
    """Bot configuration class"""
    
    # Bot settings
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # Redis settings
    # Render.com se milne wala internal Redis URL yahan ayega
    REDIS_URL = os.getenv('REDIS_URL')

    # File settings
    MAX_FILE_SIZE_MB = 20
    SUPPORTED_FORMATS = ['JPEG', 'JPG', 'PNG', 'WEBP']
    
    # Image processing settings
    MAX_IMAGE_WIDTH = 2048
    MAX_IMAGE_HEIGHT = 2048
    PRODUCT_SCALE_FACTOR = 0.7  # Product image will be 70% of template size
    
    # Template settings
    TEMPLATE_QUALITY = 95
    OUTPUT_FORMAT = 'JPEG'
    
    # Directories
    # Ab hum local directories ka istemal kam karenge, khaas kar templates ke liye
    TEMP_DIR = 'temp'
    
    # Messages
    WELCOME_MESSAGE = """
🤖 Welcome to Background Removal Bot!

I can help you remove backgrounds from product images and overlay them on your templates.

📋 Here's how it works:
1. First, send me a template image
2. I'll set it as your template
3. Then send me product images
4. I'll remove the background and overlay on your template

📸 Please send your template image now:
"""
    
    TEMPLATE_SET_MESSAGE = """
✅ Template set successfully!

Now you can send me product images and I'll remove the background and overlay them on your template.

📸 Send me a product image to process:
"""
    
    PROCESSING_MESSAGE = """
🔄 Processing your image...
⏳ Removing background and applying template...
"""
    
    SUCCESS_MESSAGE = """
✅ Background removed and applied to your template!

Send another product image to process more, or use /start to change template.
"""
    
    ERROR_MESSAGES = {
        'invalid_image': '❌ Invalid image format. Please send a valid image.',
        'processing_error': '❌ Error processing image. Please try again.',
        'template_not_found': '❌ Template not found. Please use /start to set a new template.',
        'file_too_large': '❌ File too large. Please send an image smaller than {}MB.',
        'general_error': '❌ An error occurred while processing your request. Please try again.'
    }
    
    @classmethod
    def get_max_file_size_bytes(cls):
        """Get max file size in bytes"""
        return cls.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @classmethod
    def is_supported_format(cls, format_name):
        """Check if image format is supported"""
        return format_name.upper() in cls.SUPPORTED_FORMATS
    
    @classmethod
    def get_error_message(cls, error_type, **kwargs):
        """Get formatted error message"""
        message = cls.ERROR_MESSAGES.get(error_type, cls.ERROR_MESSAGES['general_error'])
        if kwargs:
            return message.format(**kwargs)
        return message
