# Django Pulse

Backend engine for the `pulse-rn` React Native library.

## Quick Start

1. Install: `pip install django-pulse`
2. Add to `INSTALLED_APPS`:
   ```python
   INSTALLED_APPS = [
       ...,
       'channels',
       'django_pulse',
   ]
   ```

## Model Inheritance

To enable synchronization for your models, inherit from `SyncModel` instead of `models.Model`:

```python
from django_pulse.models import SyncModel
from django.db import models

class Task(SyncModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

class Item(SyncModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

### SyncModel Features

When you inherit from `SyncModel`, your models automatically get these fields:

| Field | Type | Description |
|--------|------|-------------|
| `sync_id` | UUIDField | Unique identifier for synchronization |
| `version` | PositiveIntegerField | Version number for conflict resolution |
| `is_local_only` | BooleanField | Marks records pending sync |
| `sync_error` | TextField | Stores sync error messages |
| `created_at` | DateTimeField | Auto-created timestamp |
| `updated_at` | DateTimeField | Auto-updated timestamp |

### Automatic Synchronization

All models inheriting from `SyncModel` will:

- Automatically generate UUID `sync_id` on creation
- Increment `version` on each update
- Track synchronization status with `is_local_only`
- Log synchronization errors in `sync_error`
- Participate in real-time WebSocket updates

### User-Specific Sync

If your model has a `user` field (ForeignKey to User), synchronization will be scoped to that user:

```python
class Task(SyncModel):
    title = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User-specific sync
```

Models without a `user` field will sync globally to all connected clients.

## WebSocket Configuration

Add the WebSocket routing to your `asgi.py`:

```python
from django_pulse.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        websocket_urlpatterns
    ),
})
```

## Required Settings

Ensure these settings are configured in your `settings.py`:

```python
# Channels configuration
ASGI_APPLICATION = 'your_project.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
```

## Synchronization Flow

1. **Client Connects**: WebSocket connection established
2. **Delta Sync Request**: Client requests changes since last version
3. **Batch Upload**: Client uploads pending local changes
4. **Real-time Updates**: Server pushes changes to connected clients
5. **Conflict Resolution**: Server resolves version conflicts

## Example Usage

```python
# Create a synced task
task = Task.objects.create(
    title="Complete project",
    description="Finish Django Pulse library",
    user=request.user
)

# Update with automatic version increment
task.title = "Updated project title"
task.save()  # Automatically increments version

# All changes are automatically synced to connected mobile clients