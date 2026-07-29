def validate_url(url):
    """Check if string is supported video URL"""
    if not url or url.strip() == "":
        return False
    
    url = url.strip()

    if url.startswith(('http://', 'https://', 'www.')):
        return True

    video_platforms = ['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com']
    for platform in video_platforms:
        if platform in url.lower():
            return True
    
    return False
