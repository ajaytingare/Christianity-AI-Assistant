"""
Async-safe file operations for handling uploads.
Prevents blocking the event loop.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
import logging

logger = logging.getLogger(__name__)


async def save_upload_file_async(
    file_path: str,
    contents: bytes,
    max_size_mb: int = 50
) -> Tuple[bool, Optional[str]]:
    """
    Asynchronously save uploaded file without blocking.
    
    Args:
        file_path: Destination file path
        contents: File contents as bytes
        max_size_mb: Maximum file size in MB
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Validate size
        file_size_mb = len(contents) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return False, f"File too large: {file_size_mb:.2f}MB > {max_size_mb}MB"
        
        # Create parent directory if needed
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Use async file operations
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(contents)
        
        logger.info(f"✅ File saved: {file_path} ({file_size_mb:.2f}MB)")
        return True, None
        
    except Exception as e:
        logger.error(f"❌ Error saving file: {e}")
        return False, str(e)


async def read_file_async(file_path: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Asynchronously read file without blocking.
    
    Args:
        file_path: Path to file to read
    
    Returns:
        Tuple of (contents, error_message)
    """
    try:
        async with aiofiles.open(file_path, 'rb') as f:
            contents = await f.read()
        return contents, None
    except Exception as e:
        logger.error(f"❌ Error reading file: {e}")
        return None, str(e)


def run_sync_in_executor(func, *args, **kwargs):
    """
    Run synchronous function in thread pool to avoid blocking event loop.
    
    Args:
        func: Synchronous function to run
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Coroutine that returns function result
    """
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, func, *args)
