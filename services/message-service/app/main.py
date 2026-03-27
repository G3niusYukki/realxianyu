"""Message Service - FastAPI application entry point."""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from xianyuflow_common import (
    HealthCheckResponse,
    KafkaClient,
    KafkaConfig,
    ServiceConfig,
    get_logger,
)

from app.handler import MessageHandler
from app.reply import QuoteInfo, ReplyComposer, ReplyType
from app.websocket import ConnectionStatus, WebSocketConnectionPool

logger = get_logger(__name__)

# Global instances
connection_pool: WebSocketConnectionPool
message_handler: MessageHandler
reply_composer: ReplyComposer
kafka_client: KafkaClient | None = None


class SendMessageRequest(BaseModel):
    """Request to send a message."""

    account_id: str = Field(..., description="Source account ID")
    recipient_id: str = Field(..., description="Recipient ID")
    conversation_id: str = Field(..., description="Conversation ID")
    content: str = Field(..., description="Message content")
    message_type: str = Field(default="text", description="Message type")


class SendMessageResponse(BaseModel):
    """Response for send message request."""

    success: bool = Field(..., description="Whether message was sent")
    message_id: str | None = Field(default=None, description="Message ID if sent")
    error: str | None = Field(default=None, description="Error message if failed")


class ConnectionStatusResponse(BaseModel):
    """Connection status response."""

    account_id: str = Field(..., description="Account ID")
    status: str = Field(..., description="Connection status")
    message_count: int = Field(default=0, description="Messages sent/received")
    error_count: int = Field(default=0, description="Error count")
    reconnect_attempts: int = Field(default=0, description="Reconnection attempts")
    last_ping: float | None = Field(default=None, description="Last ping timestamp")


class ConnectionsResponse(BaseModel):
    """All connections status response."""

    total: int = Field(..., description="Total connections")
    connected: int = Field(..., description="Connected count")
    connections: list[ConnectionStatusResponse] = Field(..., description="Connection details")


class QuoteCalculatedEvent(BaseModel):
    """Quote calculated event from Kafka."""

    quote_id: str = Field(..., description="Quote ID")
    account_id: str = Field(..., description="Account ID")
    conversation_id: str = Field(..., description="Conversation ID")
    buyer_id: str = Field(..., description="Buyer ID")
    original_price: float = Field(..., description="Original price")
    quoted_price: float = Field(..., description="Quoted price")
    shipping_cost: float | None = Field(default=None, description="Shipping cost")
    shipping_included: bool = Field(default=False, description="Shipping included")
    notes: str | None = Field(default=None, description="Additional notes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global connection_pool, message_handler, reply_composer, kafka_client

    # Initialize
    config = ServiceConfig()

    # Create connection pool
    connection_pool = WebSocketConnectionPool(
        max_reconnect_attempts=5,
        reconnect_base_delay=1.0,
        reconnect_max_delay=60.0,
        health_check_interval=30.0,
    )
    await connection_pool.start()

    # Create message handler
    ai_service_url = os.getenv("AI_SERVICE_URL", "http://ai-service:8000")
    message_handler = MessageHandler(
        connection_pool=connection_pool,
        ai_service_url=ai_service_url,
        auto_reply=True,
        reply_delay=1.0,
    )

    # Create reply composer
    reply_composer = ReplyComposer()

    # Initialize Kafka client if configured
    kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if kafka_bootstrap:
        kafka_config = KafkaConfig(bootstrap_servers=kafka_bootstrap)
        kafka_client = KafkaClient(kafka_config)
        kafka_client.connect()

        # Start quote event consumer
        asyncio.create_task(_consume_quote_events())

    logger.info("Message Service started")

    yield

    # Cleanup
    if message_handler:
        await message_handler.close()

    if connection_pool:
        await connection_pool.stop()

    if kafka_client:
        kafka_client.disconnect()

    logger.info("Message Service stopped")


async def _consume_quote_events() -> None:
    """Consume quote.calculated events from Kafka."""
    if not kafka_client:
        return

    def handle_quote_event(message: dict[str, Any]) -> None:
        """Handle quote calculated event."""
        try:
            event = QuoteCalculatedEvent(**message)
            logger.info(
                "Received quote event: quote_id=%s, account_id=%s",
                event.quote_id,
                event.account_id,
            )

            # Compose price quote reply
            quote_info = QuoteInfo(
                original_price=event.original_price,
                quoted_price=event.quoted_price,
                shipping_cost=event.shipping_cost,
                shipping_included=event.shipping_included,
                notes=event.notes,
            )

            reply_text = reply_composer.compose_price_reply(
                text="感谢您的咨询，为您提供报价如下：",
                quote_info=quote_info,
                context={"conversation_id": event.conversation_id},
            )

            # Send reply via WebSocket
            asyncio.create_task(
                connection_pool.send_message(
                    event.account_id,
                    {
                        "type": "text",
                        "content": reply_text,
                        "recipient_id": event.buyer_id,
                        "conversation_id": event.conversation_id,
                        "quote_id": event.quote_id,
                    },
                )
            )

        except Exception as e:
            logger.error("Error handling quote event: %s", e)

    # This would run in a separate thread in production
    # For now, we'll just log that we would consume
    logger.info("Quote event consumer would start here")


app = FastAPI(
    title="Message Service",
    description="XianyuFlow Message Service - WebSocket connection and message reply management",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return HealthCheckResponse(
        status="ok",
        version="0.1.0",
    )


@app.websocket("/ws/{account_id}")
async def websocket_endpoint(websocket: WebSocket, account_id: str) -> None:
    """WebSocket endpoint for account connections.

    Args:
        websocket: WebSocket connection.
        account_id: Xianyu account ID.
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted for account %s", account_id)

    try:
        # Register connection
        await connection_pool.register_connection(
            account_id=account_id,
            websocket=websocket,
            metadata={"connected_at": asyncio.get_event_loop().time()},
        )

        # Keep connection alive and handle messages
        # The actual message handling is done by the connection pool
        while True:
            try:
                # Wait for messages (they're handled by the pool's handler)
                data = await websocket.receive_text()
                # Echo back to confirm receipt (actual processing is async)
                await websocket.send(json.dumps({"type": "ack", "received": True}))
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected for account %s", account_id)
                break
            except Exception as e:
                logger.error("Error in WebSocket for %s: %s", account_id, e)
                break

    except Exception as e:
        logger.error("WebSocket error for account %s: %s", account_id, e)
    finally:
        await connection_pool.unregister_connection(account_id)
        logger.info("WebSocket connection closed for account %s", account_id)


@app.post("/api/v1/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest) -> SendMessageResponse:
    """Send a message to a recipient.

    Args:
        request: Send message request.

    Returns:
        Send message response.
    """
    try:
        message = {
            "type": request.message_type,
            "content": request.content,
            "recipient_id": request.recipient_id,
            "conversation_id": request.conversation_id,
            "timestamp": asyncio.get_event_loop().time(),
        }

        success = await connection_pool.send_message(request.account_id, message)

        if success:
            return SendMessageResponse(
                success=True,
                message_id=f"msg_{asyncio.get_event_loop().time()}",
            )
        else:
            return SendMessageResponse(
                success=False,
                error="Failed to send message - connection not available",
            )

    except Exception as e:
        logger.error("Error sending message: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@app.get("/api/v1/connections", response_model=ConnectionsResponse)
async def get_connections() -> ConnectionsResponse:
    """Get all connection statuses.

    Returns:
        Connections status response.
    """
    connections = connection_pool.get_all_connections()

    connection_list = []
    connected_count = 0

    for account_id, conn_info in connections.items():
        if conn_info.status == ConnectionStatus.CONNECTED:
            connected_count += 1

        connection_list.append(
            ConnectionStatusResponse(
                account_id=account_id,
                status=conn_info.status.value,
                message_count=conn_info.message_count,
                error_count=conn_info.error_count,
                reconnect_attempts=conn_info.reconnect_attempts,
                last_ping=conn_info.last_ping,
            )
        )

    return ConnectionsResponse(
        total=len(connection_list),
        connected=connected_count,
        connections=connection_list,
    )


@app.get("/api/v1/connections/{account_id}", response_model=ConnectionStatusResponse)
async def get_connection_status(account_id: str) -> ConnectionStatusResponse:
    """Get connection status for a specific account.

    Args:
        account_id: Account ID.

    Returns:
        Connection status.
    """
    conn_info = connection_pool.get_connection_status(account_id)

    if not conn_info:
        raise HTTPException(status_code=404, detail=f"Connection not found for {account_id}")

    return ConnectionStatusResponse(
        account_id=account_id,
        status=conn_info.status.value,
        message_count=conn_info.message_count,
        error_count=conn_info.error_count,
        reconnect_attempts=conn_info.reconnect_attempts,
        last_ping=conn_info.last_ping,
    )


@app.post("/api/v1/reply/compose")
async def compose_reply(
    reply_type: ReplyType,
    text: str,
    quote_info: QuoteInfo | None = None,
) -> dict[str, str]:
    """Compose a reply message.

    Args:
        reply_type: Type of reply.
        text: Base text.
        quote_info: Optional quote information.

    Returns:
        Composed reply.
    """
    composed = reply_composer.compose(
        reply_type=reply_type,
        text=text,
        quote_info=quote_info,
    )
    return {"reply": composed}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
