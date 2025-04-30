from django.contrib import admin
from .models import UserProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Define an inline admin descriptor for UserProfile model
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profiles'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_platoon')
    
    def get_role(self, obj):
        return obj.profile.get_role_display()
    get_role.short_description = 'Role'
    
    def get_platoon(self, obj):
        return obj.profile.platoon
    get_platoon.short_description = 'Platoon'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
