import jwt
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status, authentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from .. import models

class JWTAuthService ():

    def gen_tokens(self, user: models.User):
        jwt_tokens = RefreshToken.for_user(user)

        return {
                'access_token': str(jwt_tokens.access_token),
                'refresh_token': str(jwt_tokens)
                }

    def login (self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            tokens = self.gen_tokens(user)
            response = Response({"message": "successful token refresh"},
                                status=status.HTTP_200_OK)
            response.set_cookie(
                key='access_token',
                value=tokens.get('access_token'),
                httponly=True,
                secure=True,
                samesite='Lax',
            )

            response.set_cookie(
                key='refresh_token',
                value=tokens.get('refresh_token'),
                httponly=True,
                secure=True,
                samesite='Lax',
            )
            return response

        return Response({"message": "invalid login"},
                        status=status.HTTP_400_BAD_REQUEST)

    def refresh (self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        try:
            refresh_token = RefreshToken(refresh_token)
            response = Response(
                    {"message": "successful token refresh"},
                    status=status.HTTP_200_OK
                )
            response.set_cookie(
                key='access_token',
                value=str(refresh_token.access_token),
                httponly=True,
                secure=True,
                samesite='Lax',
            )
            response.set_cookie(
                key='refresh_token',
                value=str(refresh_token),
                httponly=True,
                secure=True,
                samesite='Lax',
            )
            return response

        except TokenError as e:
            return Response(#{"error": str(e)},
                            status=status.HTTP_401_UNAUTHORIZED)

    def verify (self, token):
        if not token:
            return None

        try:
            payload = jwt.decode (
                    token,
                    settings.SIMPLE_JWT.get('SIGNING_KEY'),
                    algorithms=['HS256']
                )
        except jwt.ExpiredSignatureError as e:
            raise exceptions.AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed('Invalid Token')
        except Exception as e:
            raise exceptions.AuthenticationFailed(e)

        try:
            user = models.User.objects.get(id=payload.get('user_id'))
        except models.Model.DoesNotExist:
            raise exceptions.NotFound(detail="No Such User exists")

        return (user.id, None)


    def logout (self, request):
        response = Response(status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
