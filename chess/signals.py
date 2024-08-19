from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import RegisteredUser

@receiver(post_save, sender=User)
def create_registered_user(sender, instance, created, **kwargs):
    if created:
        RegisteredUser.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_registered_user(sender, instance, **kwargs):
    instance.registereduser.save()