# bot_handler.py

import logging
import os
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes

from session_manager import SessionManager
from image_processor import ImageProcessor
from config import Config

logger = logging.getLogger(__name__)

class BotHandler:
    def __init__(self):
        self.session_manager = SessionManager()
        self.image_processor = ImageProcessor()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        logger.info(f"Processing /start for user ID: {user_id}")
        self.session_manager.reset_session(user_id)
        await update.message.reply_text(Config.WELCOME_MESSAGE)
        self.session_manager.set_user_state(user_id, 'waiting_for_template')
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.session_manager.get_user_state(user_id)
        
        if user_state == 'waiting_for_template':
            await self._handle_template_upload(update, context)
        elif user_state in ['template_set', 'collecting_images']:
            await self._handle_product_image_upload(update, context)
        else:
            await update.message.reply_text("Please use /start command first.")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.document and update.message.document.mime_type.startswith('image/'):
            await self.handle_photo(update, context)
        else:
            await update.message.reply_text("Please send only image files.")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.session_manager.get_user_state(user_id)
        text = update.message.text.strip().lower()

        if user_state == 'waiting_for_dimensions':
            await self._handle_dimensions_input(update, context, text)
        elif user_state == 'collecting_images' and text == 'done':
            await self._handle_done_collecting(update, context)
        else:
            await update.message.reply_text("I'm waiting for an image or a specific command. Use /start to begin.")

    async def _handle_template_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        processing_msg = await update.message.reply_text("📥 Downloading template image...")
        
        try:
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            
            # Download to memory instead of disk
            with BytesIO() as f:
                await file.download_to_memory(f)
                f.seek(0)
                template_data = f.read()

            # Save template data to Redis
            self.session_manager.set_template(user_id, template_data)
            self.session_manager.set_user_state(user_id, 'template_set')
            
            await processing_msg.edit_text(
                "✅ Template set successfully!\n\n"
                "Now, send me your product images. Type 'done' when you've sent all of them."
            )
        except Exception as e:
            logger.error(f"Error handling template upload: {e}")
            await processing_msg.edit_text("❌ Error processing template. Please try again.")

    async def _handle_product_image_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        processing_msg = await update.message.reply_text("📥 Downloading product image...")
        
        try:
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)

            pending_images = self.session_manager.get_pending_images(user_id)
            image_count = len(pending_images)
            
            # Save to temp directory (this is fine as it's for short-term processing)
            temp_product_path = os.path.join(Config.TEMP_DIR, f"product_{user_id}_{image_count + 1}.jpg")
            await file.download_to_drive(temp_product_path)
            
            if not self.image_processor.validate_image(temp_product_path):
                os.remove(temp_product_path)
                await processing_msg.edit_text("❌ Invalid image format.")
                return

            self.session_manager.add_pending_image(user_id, temp_product_path)
            self.session_manager.set_user_state(user_id, 'collecting_images')
            
            total_images = len(self.session_manager.get_pending_images(user_id))
            await processing_msg.edit_text(
                f"✅ Product image {total_images} received!\n\n"
                "Send more, or type 'done' when finished."
            )
        except Exception as e:
            logger.error(f"Error handling product image: {e}")
            await processing_msg.edit_text("❌ Error processing product image.")

    async def _handle_done_collecting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        pending_images = self.session_manager.get_pending_images(user_id)
        
        if not pending_images:
            await update.message.reply_text("❌ No images to process. Please send product images first.")
            self.session_manager.set_user_state(user_id, 'template_set')
            return
        
        await update.message.reply_text(
            f"✅ Great! You've sent {len(pending_images)} images.\n\n"
            "📏 Now, please tell me the dimensions for the products.\n"
            "Format: width x height (e.g., 400 x 600)"
        )
        self.session_manager.set_user_state(user_id, 'waiting_for_dimensions')

    async def _handle_dimensions_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        user_id = update.effective_user.id
        try:
            parts = [p.strip() for p in text.replace('x', ' ').split()]
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                width, height = int(parts[0]), int(parts[1])
            else:
                raise ValueError("Invalid format")

            if not (50 <= width <= 2048 and 50 <= height <= 2048):
                await update.message.reply_text("❌ Dimensions must be between 50x50 and 2048x2048.")
                return

            self.session_manager.set_dimensions(user_id, width, height)
            await self._process_product_images(update, context, width, height)

        except (ValueError, IndexError):
            await update.message.reply_text("❌ Invalid format. Please use: width x height (e.g., 500x500)")
        except Exception as e:
            logger.error(f"Error handling dimensions: {e}")
            await update.message.reply_text("❌ Error processing dimensions.")

    async def _process_product_images(self, update: Update, context: ContextTypes.DEFAULT_TYPE, width: int, height: int):
        user_id = update.effective_user.id
        
        pending_images = self.session_manager.get_pending_images(user_id)
        template_data = self.session_manager.get_template(user_id)
        
        if not pending_images or not template_data:
            await update.message.reply_text("❌ Missing images or template. Please /start over.")
            return

        total = len(pending_images)
        processing_msg = await update.message.reply_text(f"⚙️ Processing {total} images... (0/{total})")
        
        processed_count, failed_count = 0, 0
        
        for i, product_path in enumerate(pending_images, 1):
            try:
                await processing_msg.edit_text(f"⚙️ Processing {total} images... ({i}/{total})")
                
                result_path = self.image_processor.process_image_with_dimensions(
                    product_path, template_data, user_id, width, height, image_index=i
                )
                
                if result_path:
                    with open(result_path, 'rb') as photo_file:
                        await context.bot.send_photo(chat_id=user_id, photo=photo_file)
                    os.remove(result_path)
                    processed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to process image {i}: {e}")
                failed_count += 1
            finally:
                if os.path.exists(product_path):
                    os.remove(product_path)
        
        await processing_msg.edit_text(f"🎉 Processing Complete! ✅ Success: {processed_count}, ❌ Failed: {failed_count}")
        
        self.session_manager.clear_pending_images(user_id)
        self.session_manager.set_user_state(user_id, 'template_set')
        await update.message.reply_text("Send more product images, or /start to use a new template.")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Update {update} caused error {context.error}")
