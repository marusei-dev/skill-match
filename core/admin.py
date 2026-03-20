from django.contrib import admin
from .models import UserProfile, JobMatch

admin.site.register(UserProfile)
admin.site.register(JobMatch)