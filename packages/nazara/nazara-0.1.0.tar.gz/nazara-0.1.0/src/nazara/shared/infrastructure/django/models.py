import uuid

from django.db import models


class BaseModel(models.Model):
    """Base model with common fields for all Nazara models."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1, help_text="Optimistic locking version")

    class Meta:
        abstract = True
