import os

def format_file_size(size_bytes):
    """Convert bytes to human-readable string"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_safe_path_preview(full_path, max_length=50):
    """Truncate path for UI display"""
    if len(full_path) <= max_length:
        return full_path
    
    filename = os.path.basename(full_path)
    if len(filename) < max_length - 10:
        directory = os.path.dirname(full_path)
        available_length = max_length - len(filename) - 4
        if available_length > 0:
            truncated_dir = directory[:available_length]
            return f"{truncated_dir}...//{filename}"
    
    return full_path[:max_length-3] + "..."
