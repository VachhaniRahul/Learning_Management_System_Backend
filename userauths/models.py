from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password



class User(AbstractUser):
    username = models.CharField(unique=True,max_length=200)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=1000)
    otp = models.CharField(max_length=100, null=True, blank=True)
    refresh_token = models.CharField(max_length=1000,null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if self.email:
            email_username = self.email.split('@')[0]

            if not self.full_name:
                self.full_name = email_username

            if not self.username:
                self.username = email_username

            if self.pk is None or not self.password.startswith('pbkdf2_'):
                self.password = make_password(self.password)

        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.FileField(upload_to='users', default='default-user.jpg', null=True, blank=True)
    full_name = models.CharField(max_length=1000)
    country = models.CharField(max_length=100, blank=True, null=True)
    about = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.full_name:
            return self.full_name
        return str(self.user.full_name)








