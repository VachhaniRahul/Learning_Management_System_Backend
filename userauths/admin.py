from django.contrib import admin
from .models import User, Profile


class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'last_login']
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'country', 'date']

admin.site.register(User, UserAdmin)
admin.site.register(Profile)
