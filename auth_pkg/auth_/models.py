from django.db import models
from django.contrib.auth.models import AbstractUser

class User (AbstractUser):
    pass

class Session (models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255)
    expiry = models.DateTimeField()
