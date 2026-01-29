from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SyncModel, GlobalSyncSequence, SyncLog
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.forms.models import model_to_dict

@receiver(post_save)
def auto_track_sync_models(sender, instance, created, **kwargs):
    if not isinstance(instance, SyncModel):
        return

    next_v = GlobalSyncSequence.get_next_version()
    sender.objects.filter(pk=instance.pk).update(version=next_v)
    instance.version = next_v # Actualiza el objeto en memoria antes de serializar

    SyncLog.objects.create(
        content_object=instance,
        action='CREATE' if created else 'UPDATE',
        version=next_v,
        user_id=getattr(instance, 'user_id', None) # Intenta obtener user_id si existe
    )

    channel_layer = get_channel_layer()
    
    groups = instance.get_sync_groups()
    for group in groups:
        async_to_sync(channel_layer.group_send)(
            f"{group}_sync",
            {
                "type": "sync.message",
                "payload": {
                    "model": sender.__name__.lower(),
                    "sync_id": str(instance.sync_id),
                    "version": next_v,
                    "data": model_to_dict(instance)
                }
            }
        )

@receiver(post_delete)
def handle_hard_delete(sender, instance, **kwargs):
    if not isinstance(instance, SyncModel):
        return

    channel_layer = get_channel_layer()
    
    groups = instance.get_sync_groups()
    
    for group in groups:
        async_to_sync(channel_layer.group_send)(
            f"{group}_sync",
            {
                "type": "sync.message",
                "payload": {
                    "type": "HARD_DELETE",
                    "model": sender.__name__.lower(),
                    "sync_id": str(instance.sync_id),
                }
            }
        )