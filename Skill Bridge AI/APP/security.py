import os, hashlib, hmac, secrets, time, base64, json

SECRET = os.getenv("SECRET_KEY", "dev-only-change-this-secret-before-deployment")

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 180000)
    return base64.b64encode(salt + digest).decode()

def verify_password(password: str, stored: str) -> bool:
    try:
        raw = base64.b64decode(stored.encode())
        salt, expected = raw[:16], raw[16:]
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 180000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def create_token(user_id: int, role: str) -> str:
    header = _b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    payload = _b64(json.dumps({"sub":str(user_id),"role":role,"exp":int(time.time())+86400}).encode())
    signing = f"{header}.{payload}".encode()
    sig = _b64(hmac.new(SECRET.encode(), signing, hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"

def read_token(token: str):
    try:
        header, payload, signature = token.split(".")
        signing = f"{header}.{payload}".encode()
        expected = _b64(hmac.new(SECRET.encode(), signing, hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if data.get("exp", 0) < time.time():
            return None
        return data
    except Exception:
        return None
