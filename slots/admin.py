from django.contrib import admin

from .models import Slot


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    pass
