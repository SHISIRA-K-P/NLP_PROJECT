from django.contrib import admin

from .models import EmergencyAuthority


@admin.register(EmergencyAuthority)
class EmergencyAuthorityAdmin(admin.ModelAdmin):
    list_display = (
        'authority_name',
        'authority_type',
        'location_id',
        'district',
        'is_active',
        'is_verified',
    )
    list_filter = ('authority_type', 'district', 'is_active', 'is_verified')
    search_fields = ('authority_name', 'district', 'email', 'phone_number')
