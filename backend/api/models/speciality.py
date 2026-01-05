from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_delete
from django.dispatch import receiver

from ..mixin import AuditMixin

class Speciality(AuditMixin, models.Model):
    name = models.CharField(max_length=180, unique=True)
    image = models.FileField(upload_to='speciality', null=False, blank=False)

    # Attributes for soft-delete
    is_removed = models.BooleanField(default=False, db_index=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
@receiver(post_delete, sender=Speciality)
def speciality_file_cleanup(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)