import hashlib
import base64
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    api_key_encrypted = db.Column(db.String(512), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def _get_fernet(self, secret_key):
        from cryptography.fernet import Fernet
        key = base64.urlsafe_b64encode(hashlib.sha256(secret_key.encode()).digest())
        return Fernet(key)

    def save_api_key(self, api_key, secret_key):
        """Encrypt and store the API key."""
        f = self._get_fernet(secret_key)
        self.api_key_encrypted = f.encrypt(api_key.encode()).decode()

    def load_api_key(self, secret_key):
        """Decrypt and return the stored API key, or None if not set / key changed."""
        if not self.api_key_encrypted:
            return None
        try:
            f = self._get_fernet(secret_key)
            return f.decrypt(self.api_key_encrypted.encode()).decode()
        except Exception:
            return None

    def clear_api_key(self):
        self.api_key_encrypted = None

    def __repr__(self):
        return f'<User {self.username}>' 