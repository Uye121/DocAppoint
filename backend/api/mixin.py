from typing import Any
from django.db import models
from django.utils import timezone
from django.conf import settings
from rest_framework.serializers import BaseSerializer

from .utils.case import to_camelcase_data, to_snake_case_data

class TimestampMixin(models.Model):
    created_at = models.DateTimeField(db_index=True, default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class AuditMixin(models.Model):
    # use '+' to not create backwards relation
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='+'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='+'
    )

    class Meta:
        abstract = True

class CamelCaseMixin(BaseSerializer):
    def to_representation(self, instance: Any) -> dict[str, Any]:
        representation = super().to_representation(instance)
        return to_camelcase_data(representation)

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        return super().to_internal_value(to_snake_case_data(data))