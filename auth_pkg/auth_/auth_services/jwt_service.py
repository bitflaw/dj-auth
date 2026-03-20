from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status

class JWTAuthService ():
    def gen_tokens(self, user: User):
        jwt_tokens = RefreshToken.for_user(user)

        return {
                'refresh_token': str(jwt_tokens),
                'access_token': str(jwt_tokens.access_token)
                }

    def login (self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        # print (f"Username: {username}, password: {password}")

        user = authenticate(username=username, password=password)
        print (f"User: {user}")
        if user is not None:
            tokens = self.gen_tokens(user)
            response = Response({"access_token": tokens.get('access_token')},
                                status=status.HTTP_200_OK)

            response.set_cookie(
                key='refresh_token',
                value=tokens.get('refresh_token'),
                httponly=True,
                secure=True,
                samesite='Lax',
            )
            return response

        return Response({"error": "invalid login"},
                        status=status.HTTP_400_BAD_REQUEST)

    def refresh (self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        try:
            refresh_token = RefreshToken(refresh_token)
            response = Response(
                { "access_token": str(refresh_token.access_token) },
                status=status.HTTP_200_OK
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
            return Response({"error": str(e)},
                            status=status.HTTP_401_UNAUTHORIZED)

    def logout (self):
        response = Response(status=status.HTTP_200_OK)

        response.set_cookie(
            key='refresh_token',
            value='',
            httponly=True,
            secure=True,
            samesite='Lax',
            max_age=0
        )
        return response

