from django.contrib import admin

# Register your models here.
from .models import Club, Region
admin.site.register(Club)
admin.site.register(Region)
