
HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

def sanitize_headers(headers):
    """Filter hop-by-hop headers"""
    return {
        k: v
        for k, v in dict(headers).items()
        if k.lower() not in {
            "host",
            "content-length",
            "transfer-encoding",
            "connection",
        }
    }
