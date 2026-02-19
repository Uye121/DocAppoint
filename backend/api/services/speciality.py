from typing import Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from ..models import Speciality


class SpecialityService:
    @staticmethod
    def get_all_specialities(active_only: bool = True) -> QuerySet[Speciality]:
        """Get all specialities"""
        queryset = Speciality.objects.all()
        if active_only:
            queryset = queryset.filter(is_removed=False)
        return queryset.order_by("name")

    @staticmethod
    def get_speciality_by_id(speciality_id: int) -> Optional[Speciality]:
        try:
            return Speciality.objects.get(id=speciality_id, is_removed=False)
        except Speciality.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def create_speciality(name: str, image) -> Speciality:
        if Speciality.objects.filter(name__iexact=name, is_removed=False).exists():
            raise ValidationError("Speciality with this name already exists")

        speciality = Speciality.objects.create(name=name, image=image)
        return speciality

    @staticmethod
    @transaction.atomic
    def update_speciality(
        speciality: Speciality, name: Optional[str] = None, image=None
    ) -> Speciality:
        # Check non-soft-deleted speciality on name change
        if name and name != speciality.name:
            if (
                Speciality.objects.filter(name__iexact=name, is_removed=False)
                .exclude(id=speciality.id)
                .exists()
            ):
                raise ValidationError("Speciality with this name already exists")
            speciality.name = name

        if image is not None:
            speciality.image = image

        speciality.save()
        return speciality

    @staticmethod
    @transaction.atomic
    def soft_delete_speciality(speciality: Speciality) -> None:
        if speciality.provider_speciality.filter(is_removed=False).exists():
            raise ValidationError(
                "Cannot delete speciality that has active healthcare providers"
            )

        speciality.is_removed = True
        speciality.removed_at = timezone.now()
        speciality.save()
