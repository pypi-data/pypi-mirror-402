import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.apps import apps
from django.db import transaction
class SyncConsumer(AsyncWebsocketConsumer):

    def get_model_by_name(self, table_name):
        for config in apps.get_app_configs():
            try:
                return apps.get_model(config.label, table_name)
            except LookupError:
                continue
        return None

    async def connect(self):

        self.user = self.scope["user"]
        
        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}_sync"
            
            # Unirse al grupo privado del usuario en Redis
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # Este método se activa cuando la Signal envía algo a Redis
    async def sync_message(self, event):
        # Enviar el paquete de datos al móvil

        await self.send(text_data=json.dumps({
            "type": "SYNC_UPDATE",
            "data": event["payload"]
        }))

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        if msg_type == 'SYNC_BATCH_UPLOAD':
            await self.handle_batch_upload(data)
        elif msg_type == 'SYNC_UPLOAD':
            await self.handle_upload(data)
        elif msg_type == 'SYNC_REQUEST_DELTA':
            await self.handle_delta_request(data)

    async def handle_delta_request(self, data):
        table_name = data.get('table')
        last_version = data.get('last_version', 0)
        model = self.get_model_by_name(table_name)
        
        if model:
            @sync_to_async
            def get_updates():
               # Filtramos por versión y opcionalmente por usuario
                qs = model.objects.filter(version__gt=last_version)
                if hasattr(model, 'user_id'):
                    qs = qs.filter(user_id=self.user.id)
                
                return [
                    {
                        "model": table_name,
                        "sync_id": str(obj.sync_id),
                        "version": obj.version,
                        "data": obj.to_dict() 
                    } for obj in qs
                ]
            
            changes = await get_updates()
            for change in changes:
                await self.send(text_data=json.dumps({
                    "type": "SYNC_UPDATE",
                    "data": change
                }))

    async def handle_upload(self, data):
        table_name = data.get('table')
        payload = data.get('payload')
        model = self.get_model_by_name(table_name)
        if not model: return

        @sync_to_async
        def process_individual():
            sync_id = payload.get('sync_id')
            client_version = payload.get('version', 0)
            
            current_obj = model.objects.filter(sync_id=sync_id).first()
            if current_obj and client_version < current_obj.version:
                return {"status": "CONFLICT", "sync_id": sync_id}

            # manejo de errores (NACK)
            try:
                exclude = ['id', 'version', 'is_local_only']
                clean_data = {k: v for k, v in payload.items() if k not in exclude}
                if 'is_deleted' in clean_data:
                    clean_data['is_deleted'] = bool(clean_data['is_deleted'])

                model.objects.update_or_create(sync_id=sync_id, defaults=clean_data)
                return {"status": "SUCCESS", "sync_id": sync_id}
            except Exception as e:
                return {"status": "ERROR", "sync_id": sync_id, "error": str(e)}

        result = await process_individual()
        await self.send(text_data=json.dumps({
            "type": "SYNC_ACK_INDIVIDUAL",
            "table": table_name,
            **result
        }))

    async def handle_batch_upload(self, data):
        table_name = data.get('table')
        payloads = data.get('payloads', [])
        model = self.get_model_by_name(table_name)
        if not model: return

        @sync_to_async
        def process_atomic_batch():
            results = {"synced_ids": [], "conflicts": [], "errors": []}
            with transaction.atomic():
                for item in payloads:
                    s_id = item.get('sync_id')
                    c_ver = item.get('version', 0)
                    
                    curr = model.objects.filter(sync_id=s_id).first()
                    if curr and c_ver < curr.version:
                        results["conflicts"].append(s_id)
                        continue

                    try:
                        exclude = ['id', 'version', 'is_local_only']
                        clean = {k: v for k, v in item.items() if k not in exclude}
                        model.objects.update_or_create(sync_id=s_id, defaults=clean)
                        results["synced_ids"].append(s_id)
                    except Exception as e:
                        results["errors"].append({"id": s_id, "msg": str(e)})
            return results

        res = await process_atomic_batch()
        await self.send(text_data=json.dumps({
            "type": "BATCH_ACK",
            "table": table_name,
            **res
        }))