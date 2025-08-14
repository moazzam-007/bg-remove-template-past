# session_manager.py

import logging
import redis
import json
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        """Initialize session manager with Redis connection."""
        if not Config.REDIS_URL:
            raise ValueError("REDIS_URL not configured in environment variables.")
        
        try:
            self.redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            logger.info("Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}")
            raise

    def _get_user_key(self, user_id: int) -> str:
        """Generates the main key for a user's session hash."""
        return f"user:{user_id}"

    def _get_pending_images_key(self, user_id: int) -> str:
        """Generates the key for a user's pending images list."""
        return f"user:{user_id}:pending_images"

    def _get_template_key(self, user_id: int) -> str:
        """Generates the key for storing user's template image data."""
        return f"template:{user_id}"

    def set_user_state(self, user_id: int, state: str):
        """Set user state in Redis hash."""
        self.redis_client.hset(self._get_user_key(user_id), 'state', state)

    def get_user_state(self, user_id: int) -> Optional[str]:
        """Get user state from Redis hash."""
        return self.redis_client.hget(self._get_user_key(user_id), 'state')

    def set_template(self, user_id: int, template_data: bytes):
        """Set user template data in Redis."""
        # Template data is stored as bytes, not string
        self.redis_client.set(self._get_template_key(user_id), template_data)

    def get_template(self, user_id: int) -> Optional[bytes]:
        """Get user template data from Redis."""
        # Note: decode_responses=True doesn't apply to raw .get() for bytes
        redis_bytes_client = redis.from_url(Config.REDIS_URL)
        return redis_bytes_client.get(self._get_template_key(user_id))

    def add_pending_image(self, user_id: int, image_path: str):
        """Add an image path to the user's pending images list in Redis."""
        self.redis_client.rpush(self._get_pending_images_key(user_id), image_path)

    def get_pending_images(self, user_id: int) -> list:
        """Get list of pending image paths from Redis."""
        return self.redis_client.lrange(self._get_pending_images_key(user_id), 0, -1)

    def clear_pending_images(self, user_id: int):
        """Clear the pending images list from Redis."""
        self.redis_client.delete(self._get_pending_images_key(user_id))

    def set_dimensions(self, user_id: int, width: int, height: int):
        """Set target dimensions in user's session hash."""
        dims = json.dumps({'width': width, 'height': height})
        self.redis_client.hset(self._get_user_key(user_id), 'dimensions', dims)

    def get_dimensions(self, user_id: int) -> Optional[tuple]:
        """Get target dimensions from user's session hash."""
        dims_json = self.redis_client.hget(self._get_user_key(user_id), 'dimensions')
        if dims_json:
            dims = json.loads(dims_json)
            return dims.get('width'), dims.get('height')
        return None, None

    def reset_session(self, user_id: int):
        """Reset user session by deleting all related keys from Redis."""
        keys_to_delete = [
            self._get_user_key(user_id),
            self._get_pending_images_key(user_id),
            self._get_template_key(user_id)
        ]
        # Use a pipeline to delete keys atomically
        pipe = self.redis_client.pipeline()
        for key in keys_to_delete:
            pipe.delete(key)
        pipe.execute()
        logger.info(f"Session reset for user {user_id}")
