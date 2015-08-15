# create_test_admin.py
#
# Creates an admin user, done here so it can be automated as part of the reset
# script

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.create_user('admin', 'admin@admin.com', 
            'admin')
        user.first_name = 'Admin'
        user.is_staff = True
        user.is_superuser = True
        user.save()
