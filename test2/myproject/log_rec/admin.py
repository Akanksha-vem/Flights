# admin.py
from django.contrib import admin
from .models import APILog

class APILogAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'endpoint', 'parameters', 'timestamp')
    list_filter = ('method', 'timestamp', 'user')
    search_fields = ('user__username', 'endpoint', 'parameters')
    readonly_fields = ('user', 'method', 'endpoint', 'parameters', 'timestamp')


admin.site.register(APILog, APILogAdmin)
