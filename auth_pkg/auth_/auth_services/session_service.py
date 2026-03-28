import secrets
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .. import models


class SessionAuthService ():

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
            return None

        try:
            session = models.Session.objects.select_related('user_id').get(
                        session_id=token,
                        expiry__gt=datetime.now()
                        )

        except models.Session.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or expired session')

        return (session.user_id, None)


    def logout (self, request):
        session_id = request.COOKIES.get('session_id')
        logout_all = request.query_params.get('logout_all', False)

        if logout_all:
            models.Session.objects.filter(user_id=request.user.id).delete()

        models.Session.objects.get(session_id=session_id).delete()

        response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie('session_id')
        return response
