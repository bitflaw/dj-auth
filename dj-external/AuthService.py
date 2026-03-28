import os
import requests
from dotenv import load_dotenv
from rest_framework import authentication, exceptions
from . import models
from django.contrib.auth import get_user_model

load_dotenv()

# NOTE: Set AUTH_USER_MODEL in settings
User = get_user_model ()

class RemoteAuth (authentication.BaseAuthentication):

    def authenticate (self, request):

        cookie_pack = {
            "session_id": request.COOKIES.get ('session_id', None),
            "access_token": request.COOKIES.get ('access_token', None),
            # "oauth_token": request.COOKIES.get ('oauth_token', None),
        }
        try:
            response = requests.post(
                    f"{os.getenv('AUTH_MS_DOMAIN')}/auth/verify/",
                    cookies=cookie_pack
                    # timeout = 2
                    )
        except requests.exceptions.RequestException:
            raise exceptions.AuthenticationServiceException("Auth Service Down")

        if response.status_code == 200:
            uid = response.json().get('user_id')
            try:
                user = User.objects.get(id=uid)
                return (user, None)
            except models.Model.DoesNotExist:
                raise exceptions.AuthenticationFailed(detail="User does not exist!")
        return None

