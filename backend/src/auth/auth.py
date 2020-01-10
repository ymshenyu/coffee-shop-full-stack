import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev-9dxdz39b.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee'

# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header


def get_token_auth_header():
    auth = request.headers.get('Authorization')

    if not auth:
        raise AuthError({
            'message': 'Authorization header is not present.'
        }, 401)

    parts = auth.split()

    if parts[0] != 'Bearer':
        raise AuthError({
            'message': 'Authorization header must start with "Bearer".'
        }, 401)

    elif len(parts) == 1:
        raise AuthError({
            'message': 'Token not found.'
        }, 401)

    elif len(parts) > 2:
        raise AuthError({
            'message': 'Invalid header.'
        }, 401)

    token = parts[1]
    return token


def check_permissions(permission, payload):
    permissions = payload['permissions']

    if not permissions:
        raise AuthError({
            'message': 'Permission header not found.'
        }, 403)

    if permission not in permissions:
        raise AuthError({
            'message': 'Permission denied.'
        }, 401)

    return True


def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)

    if 'kid' not in unverified_header:
        raise AuthError({
            'message': 'Invalid header.'
        }, 401)

    rsa_key = {}

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if rsa_key:
        try:
            payload = jwt.decode(token, rsa_key, algorithms=ALGORITHMS,
                                 audience=API_AUDIENCE,
                                 issuer=f'https://{AUTH0_DOMAIN}/')
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'message': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'message': 'Incorrect claims.'
            }, 401)

        except Exception:
            raise AuthError({
                'message': 'Invalid header.'
            }, 401)

    else:
        raise AuthError({
            'message': "Key doesn't exist."
        }, 401)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
