import jwt
import redis
import json
from django.forms.models import model_to_dict
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status, authentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt import exceptions 
from django.conf import settings
from .. import models
# from django.db import models

class JWTAuthService ():
    rhost=settings.REDIS.get('HOST')
    rport=settings.REDIS.get('PORT')
    rdecode=settings.REDIS.get('RDECODE')
    ttl = settings.REDIS.get('TTL')

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
            response = Response({"message": "successful login"},
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
            r = redis.Redis(
                    host=self.rhost,
                    port=self.rport,
                    decode_responses=self.rdecode
                )
            user_dict = model_to_dict(user)
            res = r.setex(f"token:{tokens.get('access_token')}", self.ttl, json.dumps(user_dict, default=str))
            r.close()
            return response

        return Response({"message": "invalid login"},
                        status=status.HTTP_400_BAD_REQUEST)

    def refresh (self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        try:
            r = redis.Redis(
                    host=self.rhost,
                    port=self.rport,
                    decode_responses=self.rdecode
                )
            res = r.delete(f"token:{request.COOKIES.get('access_token')}")
            refresh_token = RefreshToken(refresh_token)
            try:
                payload = jwt.decode (
                        str(refresh_token.access_token),
                        settings.SIMPLE_JWT.get('SIGNING_KEY'),
                        algorithms=['HS256']
                        )
            except jwt.ExpiredSignatureError:
                raise exceptions.AuthenticationFailed('Token expired')
            except jwt.InvalidTokenError:
                raise exceptions.AuthenticationFailed('Invalid Token')
            except Exception as e:
                raise exceptions.AuthenticationFailed(e)

            user = models.User.objects.get(id=payload.get('user_id'))
            user_dict = model_to_dict(user)
            res = r.setex(f"token:{str(refresh_token.access_token)}", self.ttl, json.dumps(user_dict, default=str))

            r.close()

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

        except exceptions.TokenError as e:
            return Response({"message": str(e)},
                            status=status.HTTP_401_UNAUTHORIZED)
        except models.User.DoesNotExist:
            r.close()
            raise exceptions.NotFound(detail="No Such User exists")


    def verify (self, token):
        if not token:
            raise exceptions.AuthenticationFailed("Token is invalid!")

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
            r = redis.Redis(
                    host=self.rhost,
                    port=self.rport,
                    decode_responses=self.rdecode
                )
            res = r.get(f"token:{token}")
            if res == "_\r\n":
                raise exceptions.AuthenticationFailed("Invalid access token!")

            user_dict = model_to_dict(user)
            res = r.setex(f"token:{token}", self.ttl, json.dumps(user_dict, default=str))
            r.close()
            return Response(status=status.HTTP_200_OK)
        except models.Model.DoesNotExist:
            r.close()
            raise exceptions.NotFound(detail="No Such User exists")


    def logout (self, request):
        response = Response(status=status.HTTP_200_OK)
        r = redis.Redis(
                    host=self.rhost,
                    port=self.rport,
                    decode_responses=self.rdecode
                )
        res = r.delete(f"token:{request.COOKIES.get('access_token')}")
        r.close()
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
