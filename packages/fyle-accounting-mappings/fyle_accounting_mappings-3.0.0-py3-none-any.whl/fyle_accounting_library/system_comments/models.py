import uuid
import importlib
from enum import Enum

from django.db import models

workspace_models = importlib.import_module("apps.workspaces.models")
Workspace = workspace_models.Workspace


class SystemComment(models.Model):
    """
    System Comments model for tracking backend decisions and actions.
    """
    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT, db_index=True)
    batch_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    source = models.CharField(max_length=255)
    intent = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=255, null=True, blank=True)
    entity_id = models.IntegerField(null=True, blank=True)
    export_type = models.CharField(max_length=255, null=True, blank=True)
    is_user_visible = models.BooleanField(default=False)
    detail = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'system_comments'
        indexes = [
            models.Index(fields=['workspace_id', 'source']),
            models.Index(fields=['workspace_id', 'intent']),
            models.Index(fields=['workspace_id', 'batch_id']),
            models.Index(fields=['workspace_id', 'entity_type', 'entity_id']),
        ]

    @staticmethod
    def _get_value(value):
        """
        Extract value from enum or return as-is if string.
        :param value: Enum or string value
        :returns: str
        """
        if value is None:
            return None
        if isinstance(value, Enum):
            return value.value
        return value

    @staticmethod
    def generate_batch_id() -> str:
        """
        Generate a new batch ID (UUID v4) for grouping related comments.
        :returns: str
        """
        return str(uuid.uuid4())

    @classmethod
    def create_comment(
        cls,
        workspace_id: int,
        source: Enum | str,
        intent: Enum | str,
        entity_type: Enum | str = None,
        entity_id: int | str = None,
        export_type: Enum | str = None,
        batch_id: str = None,
        is_user_visible: bool = False,
        detail: dict | str = None
    ) -> 'SystemComment':
        """
        Create a system comment.
        :param workspace_id: Workspace ID
        :param source: Source subsystem (enum or string)
        :param intent: Type of action/decision (enum or string)
        :param entity_type: Type of related entity (enum or string)
        :param entity_id: ID of related entity
        :param export_type: Export type (enum or string)
        :param batch_id: Batch ID to group related comments
        :param is_user_visible: Whether visible to end-users
        :param detail: Additional context dict
        :returns: SystemComment instance
        """
        return cls.objects.create(
            workspace_id=workspace_id,
            source=cls._get_value(source),
            intent=cls._get_value(intent),
            entity_type=cls._get_value(entity_type),
            entity_id=entity_id,
            export_type=cls._get_value(export_type),
            batch_id=batch_id or cls.generate_batch_id(),
            is_user_visible=is_user_visible,
            detail=detail or {}
        )

    @classmethod
    def bulk_create_comments(cls, comments_data: list, batch_id: str = None) -> list:
        """
        Bulk create system comments for performance.
        :param comments_data: List of dicts with comment data
        :param batch_id: Batch ID to assign to all comments
        :returns: List of SystemComment objects
        """
        shared_batch_id = batch_id or cls.generate_batch_id()

        comment_objects = []
        for c in comments_data:
            comment_objects.append(cls(
                workspace_id=c['workspace_id'],
                source=cls._get_value(c['source']),
                intent=cls._get_value(c['intent']),
                entity_type=cls._get_value(c.get('entity_type')),
                entity_id=c.get('entity_id'),
                export_type=cls._get_value(c.get('export_type')),
                batch_id=c.get('batch_id', shared_batch_id),
                is_user_visible=c.get('is_user_visible', False),
                detail=c.get('detail', {})
            ))

        return cls.objects.bulk_create(comment_objects, batch_size=50)
