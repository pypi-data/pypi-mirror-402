from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict
import uuid
import traceback
from dassco_utils.messaging import AsyncRabbitMqClient

@dataclass
class Asset:
    id: str
    info: Dict[str, Any]

@dataclass
class OrchestrationEvent:
    run_id: uuid.UUID
    idx: int
    event: str
    params: Dict[str, Any]
    asset: Asset
    reply_queue: str

class OrchestrationClient:
    def __init__(self, mq_client: AsyncRabbitMqClient, service_name: str = "unknown-service") -> None:
        self._mq = mq_client
        self._service_name = service_name
        self._handlers: Dict[str, Callable[[OrchestrationEvent], Awaitable[Dict[str, Any]]]] = {}

    def handler(self, event_name: str):
        def decorator(func: Callable[[OrchestrationEvent], Awaitable[Dict[str, Any]]]):
            self._handlers[event_name] = func
            return func
        return decorator

    async def register_handlers(self) -> None:
        for event_name, func in self._handlers.items():
            async def wrapper(payload: Dict[str, Any], _props, _func=func, _event_name=event_name):
                try:
                    evt = OrchestrationEvent(
                        run_id=uuid.UUID(payload["run_id"]),
                        idx=int(payload["idx"]),
                        event=payload["event"],
                        params=payload["params"],
                        asset=Asset(**payload["asset"]),
                        reply_queue=payload["reply_queue"],
                    )
                except Exception as e:
                    print(f"[{self._service_name}] Invalid orchestration payload for '{_event_name}': {payload} ({e})")
                    await self._send_done(
                        run_id=payload["run_id"],
                        idx=payload["idx"],
                        event=payload["event"],
                        reply_queue=payload["reply_queue"],
                        status="FAILED",
                        result={"error": f"invalid payload: {str(e)}"},
                    )
                    return

                try:
                    result = await _func(evt)
                    status = "DONE"
                except Exception as e:
                    print(f"[{self._service_name}] Handler '{_event_name}' failed: {e}")
                    traceback.print_exc()
                    status = "FAILED"
                    result = {
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    }

                await self._send_done(
                    run_id=str(evt.run_id),
                    idx=evt.idx,
                    event=evt.event,
                    reply_queue=evt.reply_queue,
                    status=status,
                    result=result,
                )

            await self._mq.add_handler(event_name, handler=wrapper)

    async def _send_done(
            self,
            run_id: str,
            idx: int,
            event: str,
            reply_queue: str,
            status: str,
            result: Dict[str, Any]
    ) -> None:
        payload = {
            "run_id": run_id,
            "idx": idx,
            "event": event,
            "status": status,
            "result": result,
        }
        await self._mq.publish(reply_queue, payload)