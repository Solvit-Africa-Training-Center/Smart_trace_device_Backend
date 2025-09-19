from django.contrib import admin

from authentication.models import VerificationCode
from .models import *

class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'serial_number', 'name', 'category', 'created_at', 'updated_at', 'device_image')

class MatchAdmin(admin.ModelAdmin):
    list_display = ('lost_item', 'found_item', 'match_status', 'match_date')

class ReturnAdmin(admin.ModelAdmin):
    list_display = ('lost_item', 'found_item', 'owner', 'finder', 'return_date', 'confirmation')

class LostItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'serial_number', 'name', 'category', 'created_at', 'updated_at', 'device_image')

admin.site.register(Device, DeviceAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Return, ReturnAdmin)
admin.site.register(LostItem, )
admin.site.register(FoundItem, )
