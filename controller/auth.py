from flask import request
import logging
import jwt

from config import JWT_SECRET

def get_token():
    """
    Get the token from the authorization header.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    return auth_header[7:]

def decode_token(token):
    """
    Decode the token using the JWT_SECRET.
    """
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return decoded
    except jwt.ExpiredSignatureError:
        logging.error("JWT token has expired")
        return None
    except jwt.InvalidTokenError:
        logging.error("Invalid JWT token")
        return None

def is_authorized(token, required_roles):
    """
    Check if the user is authorized to perform the requested action.
    """
    decoded = decode_token(token)
    if not decoded:
        return False
    user_roles = decoded.get('roles', [])
    for role in required_roles:
        if role in user_roles:
            return True
    return False