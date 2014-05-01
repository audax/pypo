from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as OriginalUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class UserAdmin(OriginalUserAdmin):
    inlines = [UserProfileInline]

try:
    admin.site.unregister(User)
finally:
    admin.site.register(User, UserAdmin)

