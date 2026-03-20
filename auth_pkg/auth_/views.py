from rest_framework.views import APIView
from .auth_services import *

auth_service = jwt_service.JWTAuthService()

class LoginView (APIView):

    def post (self, request):
        return auth_service.login (request)

class RefreshView (APIView):

    def post (self, request):
        return auth_service.refresh (request)

class LogoutView (APIView):

    def post (self, request):
        return auth_service.logout ()
