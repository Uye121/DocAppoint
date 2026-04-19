from typing import Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Speciality


class SpecialityService:
    @staticmethod
    def get_all_specialities(active_only: bool = True) -> QuerySet[Speciality]:
        """
        Retrieve all specialities, optionally filtering to active ones only.

        Args:
            active_only (bool): If True, only return non-removed specialities.
                               Defaults to True.

        Returns:
            QuerySet[Speciality]: Ordered queryset of specialities by name.
        """
        queryset = Speciality.objects.all()
        if active_only:
            queryset = queryset.filter(is_removed=False)
        return queryset.order_by("name")

    @staticmethod
    def get_speciality_by_id(speciality_id: int) -> Optional[Speciality]:
        """
        Retrieve a single speciality by ID, only if it's not soft-deleted.

        Args:
            speciality_id (int): The primary key of the speciality.

        Returns:
            Optional[Speciality]: The speciality instance if found and active,
                                  None otherwise.
        """
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
        speciality: Speciality,
        name: Optional[str] = None,
        image: Optional[SimpleUploadedFile] = None,
    ) -> Speciality:
        """
        Update an existing speciality's name and/or image.

        Args:
            speciality (Speciality): The speciality instance to update.
            name (Optional[str]): New name for the speciality. If None, name unchanged.
            image (Optional[Union[SimpleUploadedFile, str]]): New image for the speciality.
                                                             If None, image unchanged.

        Returns:
            Speciality: The updated speciality instance.
        """
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
        """
        Soft-delete a speciality by marking it as removed.

        Args:
            speciality (Speciality): The speciality instance to soft-delete.

        Returns:
            None
        """
        if speciality.provider_speciality.filter(is_removed=False).exists():
            raise ValidationError(
                "Cannot delete speciality that has active healthcare providers"
            )

        speciality.is_removed = True
        speciality.removed_at = timezone.now()
        speciality.save()
