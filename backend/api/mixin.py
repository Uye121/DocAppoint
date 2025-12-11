from django.db import models
from django.utils import timezone

from models import User

class TimestampMixin(models.Model):
    created_at = models.DateTimeField(db_index=True, default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class AuditMixin(models.Model):
    # use '+' to not create backwards relation
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

    class Meta:
        abstract = True