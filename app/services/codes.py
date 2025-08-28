# app/services/codes.py
def make_code(prefix: str, n: int, width: int = 6) -> str:
    return f"{prefix}{n:0{width}d}"
