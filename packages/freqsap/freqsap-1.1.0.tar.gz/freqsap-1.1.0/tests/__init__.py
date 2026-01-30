import socket


def internet(host: str = "8.8.8.8", port: int = 53, timeout: int = 3):
    """Host: 8.8.8.8 (google-public-dns-a.google.com).

    OpenPort: 53/tcp
    Service: domain (DNS/TCP).
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError:
        return False
