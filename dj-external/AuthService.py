import os
import redis
import json
import requests
from . import models
from dotenv import load_dotenv
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

load_dotenv()

# NOTE: Set AUTH_USER_MODEL in settings
User = get_user_model ()

class RemoteAuth (authentication.BaseAuthentication):

    def redis_get_n_convert (self, r, token):
        cached_user = r.get(f"token:{token}")
        if cached_user is None:
            return None
        user_dict = json.loads(cached_user)
        group_data = user_dict.pop('groups', [])
        perm_data = user_dict.pop('user_permissions', [])
        user = User(**user_dict)
        user.groups.set(group_data)
        user.user_permissions.set(perm_data)
        return (user, None)

    def authenticate (self, request):

        r = redis.Redis(
                host=os.getenv('REDIS_HOST'),
                port=os.getenv('REDIS_PORT'),
                decode_responses=os.getenv('REDIS_RDECODE')
                )

        session_id = request.COOKIES.get ('session_id', None)
        access_token = request.COOKIES.get ('access_token', None)
        cookie_pack = {
            "session_id": session_id,
            "access_token": access_token,
        }
        try:
            token = session_id if session_id is not None
                    elif access_token if access_token is not None
                    else None
            if token is None:
                return None
            user = redis_get_n_convert (r, token)

            if user is None:
                response = requests.post(
                        f"{os.getenv('AUTH_MS_DOMAIN')}/auth/verify/",
                        cookies=cookie_pack
                        # timeout = 2
                        )
            else:
                return user
        except requests.exceptions.RequestException:
            raise exceptions.AuthenticationServiceException("Auth Service Down")
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"{e}")

        if response.status_code == 200:
            user = redis_get_n_convert (r, token)
            if user is not None:
                return user
        return None
