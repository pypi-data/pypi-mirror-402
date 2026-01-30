import json
import asyncio
import logging
import redis.asyncio as aioredis
from django.conf import settings

from wise.utils.stream_manager import stream_manager

logger = logging.getLogger(__name__)


def get_redis_client() -> aioredis.Redis:
    redis_settings = settings.ENV.redis
    return aioredis.Redis(
        host=redis_settings.host,
        port=redis_settings.port,
        db=redis_settings.db,
        username=redis_settings.user,
        password=redis_settings.password,
    )


async def handle_message(channel: bytes, data: bytes):
    try:
        payload = json.loads(data)
    except Exception:
        payload = {"payload": data}

    dispatch_key = ":".join(channel.decode().split(":")[1:])
    event = {
        "dispatch_key": dispatch_key,
        "payload": payload,
    }

    await stream_manager.send_event(dispatch_key, event)


async def redis_subscriber(app_stop_event: asyncio.Event):
    """
    Pattern-subscribe to redis channels.
    This function returns when app_stop_event is set.
    """
    try:
        r = get_redis_client()
        pubsub = r.pubsub()

        channel_prefix = settings.ENV.redis.internal_event_channel_prefix

        await pubsub.psubscribe(f"{channel_prefix}:*")
        logger.info(f"Subscribed to Redis {channel_prefix}:* pattern")

        while not app_stop_event.is_set():
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message:
                mtype = message.get("type")
                if mtype in ("message", "pmessage"):
                    channel = message.get("channel")
                    data = message.get("data")
                    # dispatch without blocking
                    asyncio.create_task(handle_message(channel, data))
            else:
                await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("redis_subscriber exception")
    finally:
        try:
            await pubsub.close()
            await r.close()
        except Exception:
            pass
