from __future__ import annotations

import hashlib
import secrets
from urllib.parse import quote


def gen_token_key():
    key = secrets.token_urlsafe(32)
    return f'tok_{key}'


def gen_gravatar_url(email: str, name: str | None = None, size: int = 400, default: str = 'identicon'):
    email_sha = hashlib.sha256(email.encode('utf-8')).hexdigest()
    url = f'https://gravatar.com/avatar/{email_sha}?s={size}'
    if name:
        return f'{url}&d=initials&name={quote(name)}'
    else:
        return f'{url}&d={default}'
