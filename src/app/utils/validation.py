def validate_url(url):
    """Basic sanity check to ensure the string resembles a URL."""
    if not url or not url.strip():
        return False

    url = url.strip()

    # Minimal URL heuristic: must contain a dot (domain) and no spaces
    if "." in url and " " not in url:
        return True

    return False
