import base64, hashlib, hmac, json, os, time
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, salt_text, digest_text = encoded.split("$", 2)
        if scheme != "scrypt": return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def create_token(user: User) -> str:
    header = _b64(json.dumps({"alg":"HS256","typ":"JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub":str(user.id),"role":user.role,"exp":int(time.time()) + settings.jwt_expires_minutes*60}, separators=(",", ":")).encode())
    message = f"{header}.{payload}".encode()
    signature = _b64(hmac.new(settings.jwt_secret.encode(), message, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"

def _decode_token(token: str) -> dict:
    try:
        header, payload, signature = token.split(".")
        message = f"{header}.{payload}".encode()
        expected = _b64(hmac.new(settings.jwt_secret.encode(), message, hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected): raise ValueError("bad signature")
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if int(data.get("exp", 0)) <= int(time.time()): raise ValueError("expired")
        return data
    except Exception as exc:
        raise ValueError("invalid token") from exc

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session", headers={"WWW-Authenticate": "Bearer"})
    try: user_id = int(_decode_token(token).get("sub", "0"))
    except (ValueError, TypeError): raise error
    user = db.get(User, user_id)
    if not user or not user.is_active: raise error
    return user

def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin": raise HTTPException(status_code=403, detail="Admin access required")
    return user
