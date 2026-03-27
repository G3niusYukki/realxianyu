"""FastAPI application for Quote Service."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from xianyuflow_common import (
    HealthCheckResponse,
    KafkaClient,
    ServiceConfig,
    get_logger,
)
from xianyuflow_common.kafka import TOPICS

from app.cost_table import CostTableRepository
from app.engine import QuoteEngine, QuoteResult
from app.providers import MockQuoteProvider

# Configure logging
logger = get_logger(__name__)

# Global instances
config = ServiceConfig(
    name="quote-service",
    version="0.1.0",
    port=int(os.getenv("PORT", "8000")),
)
kafka_client: KafkaClient | None = None
quote_engine: QuoteEngine | None = None
cost_repository: CostTableRepository | None = None


# Pydantic models for API
from pydantic import BaseModel, Field


class QuoteCalculateRequest(BaseModel):
    """Quote calculation request."""

    origin: str = Field(..., description="Origin address/region")
    dest: str = Field(..., description="Destination address/region")
    weight: float = Field(..., gt=0, description="Weight in kg")
    volume: float | None = Field(None, gt=0, description="Volume in cubic meters")
    length: float | None = Field(None, gt=0, description="Length in cm")
    width: float | None = Field(None, gt=0, description="Width in cm")
    height: float | None = Field(None, gt=0, description="Height in cm")
    courier: str | None = Field(None, description="Preferred courier")
    is_vip: bool = Field(False, description="VIP member status")


class QuoteCalculateResponse(BaseModel):
    """Quote calculation response."""

    courier: str = Field(..., description="Courier name")
    price: float = Field(..., description="Price in CNY")
    currency: str = Field(default="CNY", description="Currency code")
    eta_days: int = Field(..., description="Estimated delivery days (min)")
    eta_days_max: int | None = Field(None, description="Estimated delivery days (max)")
    volume_formula: str | None = Field(None, description="Volume weight calculation formula")
    is_vip_price: bool = Field(False, description="Whether VIP discount applied")
    breakdown: dict[str, Any] | None = Field(None, description="Price breakdown")


class QuotesListResponse(BaseModel):
    """Multiple quotes response."""

    quotes: list[QuoteCalculateResponse]
    count: int


def create_quote_response(result: QuoteResult) -> QuoteCalculateResponse:
    """Convert QuoteResult to API response model."""
    return QuoteCalculateResponse(
        courier=result.courier,
        price=result.price,
        currency=result.currency,
        eta_days=result.eta_days,
        eta_days_max=result.eta_days_max,
        volume_formula=result.volume_formula,
        is_vip_price=result.is_vip_price,
        breakdown=result.breakdown,
    )


def handle_kafka_message(message: dict[str, Any]) -> None:
    """Handle incoming Kafka message.

    Args:
        message: Kafka message payload.
    """
    logger.debug("Received Kafka message: %s", message)

    # Handle messages.received topic
    msg_type = message.get("type")
    if msg_type == "quote_request":
        asyncio.create_task(process_quote_request(message))


async def process_quote_request(message: dict[str, Any]) -> None:
    """Process quote request from Kafka.

    Args:
        message: Quote request message.
    """
    try:
        data = message.get("data", {})
        origin = data.get("origin")
        dest = data.get("dest")
        weight = data.get("weight")

        if not all([origin, dest, weight]):
            logger.warning("Invalid quote request: %s", message)
            return

        result = await quote_engine.calculate_quote(
            origin=origin,
            dest=dest,
            weight=weight,
            courier=data.get("courier"),
            volume=data.get("volume"),
            is_vip=data.get("is_vip", False),
        )

        if result and kafka_client:
            # Publish quote.calculated event
            kafka_client.publish(
                topic="xianyuflow.quotes.calculated",
                message={
                    "type": "quote_calculated",
                    "request_id": message.get("request_id"),
                    "data": {
                        "courier": result.courier,
                        "price": result.price,
                        "currency": result.currency,
                        "eta_days": result.eta_days,
                        "origin": origin,
                        "dest": dest,
                        "weight": weight,
                    },
                },
                key=str(message.get("request_id", "")),
            )
            logger.info("Published quote.calculated for request %s", message.get("request_id"))

    except Exception as e:
        logger.error("Error processing quote request: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global kafka_client, quote_engine, cost_repository

    # Startup
    logger.info("Starting Quote Service v%s", config.version)

    # Initialize cost repository
    cost_repository = CostTableRepository()
    cost_repository.load_defaults()

    # Load custom cost tables if available
    data_path = os.getenv("COST_TABLE_PATH")
    if data_path:
        if data_path.endswith(".csv"):
            cost_repository.load_from_csv(data_path)
        elif data_path.endswith(".json"):
            cost_repository.load_from_json(data_path)

    # Initialize quote engine
    providers = [MockQuoteProvider("mock")]
    quote_engine = QuoteEngine(
        cost_repository=cost_repository,
        providers=providers,
    )

    # Initialize Kafka client
    kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    from xianyuflow_common.config import KafkaConfig

    kafka_config = KafkaConfig(
        bootstrap_servers=kafka_bootstrap,
        client_id="quote-service",
    )
    kafka_client = KafkaClient(kafka_config)

    try:
        kafka_client.connect()
        logger.info("Connected to Kafka at %s", kafka_bootstrap)

        # Start Kafka consumer in background
        consumer_task = asyncio.create_task(start_kafka_consumer())

    except Exception as e:
        logger.warning("Failed to connect to Kafka: %s", e)
        kafka_client = None

    yield

    # Shutdown
    logger.info("Shutting down Quote Service")

    if kafka_client:
        kafka_client.disconnect()


async def start_kafka_consumer() -> None:
    """Start Kafka consumer in background."""
    if not kafka_client:
        return

    try:
        # Subscribe to messages.received topic for quote requests
        kafka_client.consume(
            topics=["xianyuflow.messages.received"],
            group_id="quote-service",
            handler=handle_kafka_message,
        )
    except Exception as e:
        logger.error("Kafka consumer error: %s", e)


# Create FastAPI app
app = FastAPI(
    title="Quote Service",
    description="Logistics pricing calculation service for XianyuFlow",
    version=config.version,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return HealthCheckResponse(
        status="ok",
        version=config.version,
    )


@app.post("/api/v1/quotes/calculate", response_model=QuoteCalculateResponse)
async def calculate_quote(request: QuoteCalculateRequest) -> QuoteCalculateResponse:
    """Calculate shipping quote.

    Args:
        request: Quote calculation request.

    Returns:
        Quote calculation result.

    Raises:
        HTTPException: If quote cannot be calculated.
    """
    if not quote_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Quote engine not initialized",
        )

    # Handle dimensions
    dimensions = None
    if request.length and request.width and request.height:
        dimensions = (request.length, request.width, request.height)

    result = await quote_engine.calculate_quote(
        origin=request.origin,
        dest=request.dest,
        weight=request.weight,
        courier=request.courier,
        volume=request.volume,
        dimensions=dimensions,
        is_vip=request.is_vip,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No quote available for the given route",
        )

    # Publish quote.calculated event
    if kafka_client:
        try:
            kafka_client.publish(
                topic="xianyuflow.quotes.calculated",
                message={
                    "type": "quote_calculated",
                    "data": {
                        "courier": result.courier,
                        "price": result.price,
                        "currency": result.currency,
                        "eta_days": result.eta_days,
                        "origin": request.origin,
                        "dest": request.dest,
                        "weight": request.weight,
                        "is_vip": request.is_vip,
                    },
                },
            )
        except Exception as e:
            logger.warning("Failed to publish quote event: %s", e)

    return create_quote_response(result)


@app.post("/api/v1/quotes/calculate-all", response_model=QuotesListResponse)
async def calculate_all_quotes(request: QuoteCalculateRequest) -> QuotesListResponse:
    """Calculate quotes from all available couriers.

    Args:
        request: Quote calculation request.

    Returns:
        List of quotes from all couriers.
    """
    if not quote_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Quote engine not initialized",
        )

    # Handle dimensions
    dimensions = None
    if request.length and request.width and request.height:
        dimensions = (request.length, request.width, request.height)

    results = await quote_engine.calculate_quotes(
        origin=request.origin,
        dest=request.dest,
        weight=request.weight,
        volume=request.volume,
        dimensions=dimensions,
        is_vip=request.is_vip,
    )

    return QuotesListResponse(
        quotes=[create_quote_response(r) for r in results],
        count=len(results),
    )


@app.get("/api/v1/couriers")
async def list_couriers() -> dict[str, Any]:
    """List available couriers."""
    if not quote_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Quote engine not initialized",
        )

    return {
        "couriers": quote_engine.get_available_couriers(),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc) -> JSONResponse:
    """Global exception handler."""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
