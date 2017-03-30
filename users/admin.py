from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib import admin

from users.models import ADGroupMapping, User


class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (None, {'fields': ('department_name', 'uuid', 'favorite_resources')}),
    )

class ADGroupMappingAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(ADGroupMapping, ADGroupMappingAdmin)
