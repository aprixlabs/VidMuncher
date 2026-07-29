import os
import time
import gc
from app.utils.debug import debug_print

def cleanup_file_with_timeout(filepath, max_attempts=3, total_timeout=2):
    """Delete file with timeout, retry on PermissionError"""
    start_time = time.time()
    for attempt in range(max_attempts):
        if time.time() - start_time > total_timeout:
            break
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except PermissionError:
            time.sleep(0.1)
        except Exception:
            break
    return False

def cleanup_temp_files(temp_files_list):
    """Delete files from list in-place"""
    for temp_file in temp_files_list[:]:
        if cleanup_file_with_timeout(temp_file):
            temp_files_list.remove(temp_file)
            debug_print(f"Cleaned up temp file: {temp_file}")
        else:
            debug_print(f"Failed to clean up temp file: {temp_file}")

def force_garbage_collection():
    """Trigger GC and log memory usage"""
    collected = gc.collect()
    debug_print(f"Garbage collection freed {collected} objects")

    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        debug_print(f"Current memory usage: {memory_mb:.1f} MB")
    except ImportError:
        pass
