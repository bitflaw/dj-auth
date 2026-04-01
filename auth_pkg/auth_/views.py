from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, exceptions
from .auth_services import *

auth_service = jwt_service.JWTAuthService()
#session_service.SessionAuthService() 

class LoginView (APIView):

    def post (self, request):
        return auth_service.login (request)

class RefreshView (APIView):

    def post (self, request):
        return auth_service.refresh (request)

class LogoutView (APIView):

    def post (self, request):
        return auth_service.logout (request)

class InternalVerifyView (APIView):
    permission_classes = [AllowAny]

    def post (self, request):
        token = None
        auth_type = type(auth_service)
        if auth_type == jwt_service.JWTAuthService:
            token = request.COOKIES.get ('access_token', None)
        elif auth_type == session_service.SessionAuthService:
            token = request.COOKIES.get ('session_id', None)
        # elif auth_type == oauth_service.OAuthService:
            #token = request.COOKIES.get ('oauth_token', None)
        else:
            pass

        if token is None:
            return Response ({"message": "No token provided as cookie for verification"},
                             status=status.HTTP_400_BAD_REQUEST)
        return auth_service.verify(token)
