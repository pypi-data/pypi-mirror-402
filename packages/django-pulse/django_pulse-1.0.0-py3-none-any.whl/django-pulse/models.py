from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
import uuid

class GlobalSyncSequence(models.Model):
    last_version = models.BigIntegerField(default=0)
    
    @classmethod
    def get_next_version(cls):
        # Usamos select_for_update para bloquear la fila y evitar que 
        # dos procesos tomen el mismo número al mismo tiempo (Race Condition)
        from django.db import transaction
        with transaction.atomic():
            seq, created = cls.objects.select_for_update().get_or_create(id=1)
            seq.last_version += 1
            seq.save()
            return seq.last_version

class SyncModel(models.Model):
    # uid para evitar colisiones entre movil y servidor.
    sync_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    version = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False) 
    user_id = models.IntegerField(db_index=True, null=True, blank=True)

    class Meta:
        abstract = True

    def get_sync_groups(self):
        """
        Lógica por defecto: 
        1. Si el modelo tiene un campo 'user', enviar a ese usuario.
        2. Si no, enviar al grupo 'global'.
        """
        if hasattr(self, 'user_id') and self.user_id:
            return [f"user_{self.user_id}"]
        return ["global"]

    
    def soft_delete(self):
        self.is_deleted = True

        next_v = GlobalSyncSequence.get_next_version()
        self.version = next_v
        self.save()

    def to_dict(self):
        from django.forms.models import model_to_dict
        data = model_to_dict(self)
        data['sync_id'] = str(self.sync_id)
        if 'updated_at' in data:
            data['updated_at'] = self.updated_at.isoformat()
        return data

    def serialize_model(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        from django.forms.models import model_to_dict
        return model_to_dict(obj)

    def __str__(self):
        return f"{self.sync_id}"

class SyncLog(models.Model):
    # Apuntador genérico a cualquier objeto
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField() 
    content_object = GenericForeignKey('content_type', 'object_id')
    
    action = models.CharField(max_length=10, choices=[
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ])
    version = models.BigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Para la "Sincronización Selectiva" que hablamos
    user_id = models.IntegerField(db_index=True)


class Item(SyncModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

