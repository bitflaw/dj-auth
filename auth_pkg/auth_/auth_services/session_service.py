import secrets
import redis
import json
from django.forms.models import model_to_dict
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework_simplejwt import exceptions 
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .. import models
from django.conf import settings


class SessionAuthService ():

    rhost=settings.REDIS.get('HOST')
    rport=settings.REDIS.get('PORT')
    rdecode=settings.REDIS.get('RDECODE')
    ttl = settings.REDIS.get('TTL')

    def login (self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            unit = getattr (settings, 'SESSION_DURATION_UNIT', 'DAYS')
            duration = getattr (settings, 'SESSION_DURATION', 7)

            delta = timedelta (days=duration) if unit == 'DAYS' else timedelta (hours=duration)
            exp = timezone.now() + delta

            session_token = secrets.token_urlsafe(64)
            models.Session.objects.create (
                        user_id=user,
                        session_id=session_token,
                        expiry=exp
                    )
            user_dict = model_to_dict (user)

            r = redis.Redis(
                    host=self.rhost,
                    port=self.rport,
                    decode_responses=self.rdecode
                    )

            res = r.setex(f"token:{session_token}", self.ttl, json.dumps(user_dict, default=str))

            response = Response ({"message": "Logged in"}, status=status.HTTP_200_OK)
            response.set_cookie (
                key='session_id',
                value=session_token,
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=int(delta.total_seconds())
            )
            return response

        return Response({"message": "invalid credentials"},
                        status=status.HTTP_401_UNAUTHORIZED)

    def verify (self, token):
        if not token:
            raise exceptions.AuthenticationFailed("Session is invalid!")

        try:
            session = models.Session.objects.select_related('user_id').get(
                        session_id=token,
                        expiry__gt=timezone.now()
                        )

            r = redis.Redis(
                    host=self.rhost,
                    port=self.rport,
                    decode_responses=self.rdecode
                    )
            res = r.get(f"token:{token}")
            if res == "_\r\n":
                raise exceptions.AuthenticationFailed("Session is invalid!")

            user_dict = model_to_dict(session.user_id)
            res = r.setex(f"token:{token}", self.ttl, json.dumps(user_dict, default=str))
            r.close()

            return Response(status=status.HTTP_200_OK)
        except models.Session.DoesNotExist:
            r.close()
            raise exceptions.AuthenticationFailed('Invalid or expired session')

    def logout (self, request):
        session_id = request.COOKIES.get('session_id')
        logout_all = request.query_params.get('logout_all', False)
        r = redis.Redis(
                host=self.rhost,
                port=self.rport,
                decode_responses=self.rdecode
            )

        try:
            if logout_all:
                sessions = models.Session.objects.filter(user_id=request.user.id)
                [r.delete(f"token:{session.session_id}") for session in sessions]
            else:
                session = models.Session.objects.get(session_id=session_id)
                session.delete()
                res = r.delete(f"token:{session_id}")
        except models.Session.DoesNotExist:
            r.close()
            raise exceptions.AuthenticationFailed('Session does not exist!')

        r.close()
        response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie('session_id')
        return response
