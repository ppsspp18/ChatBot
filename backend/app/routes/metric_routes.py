from fastapi import APIRouter, Query

from backend.app.services.metric_service import (
    get_overview,
    get_latency_stats,
    get_error_stats,
    get_token_stats,
    get_throughput_stats,
)

router = APIRouter(prefix="/metrics", tags=["Metrics"])

_HOURS_DESC = "Lookback window in hours (default 24, max 168 = 7 days)"


@router.get("/overview")
async def metrics_overview(
    hours: int = Query(default=24, ge=1, le=168, description=_HOURS_DESC)
):
    """
    Summary stats for the dashboard header cards:
    total calls, total tokens, error count, avg latency, error rate.
    """
    return await get_overview(hours=hours)


@router.get("/latency")
async def metrics_latency(
    hours: int = Query(default=24, ge=1, le=168, description=_HOURS_DESC)
):
    """
    Latency percentiles (p50 / p95 / p99) + hourly time-series.
    Compatible with MongoDB M0 (no $percentile aggregation operator needed).
    """
    return await get_latency_stats(hours=hours)


@router.get("/errors")
async def metrics_errors(
    hours: int = Query(default=24, ge=1, le=168, description=_HOURS_DESC)
):
    """
    Error breakdown by provider and error type + hourly error-rate time-series.
    """
    return await get_error_stats(hours=hours)


@router.get("/tokens")
async def metrics_tokens(
    hours: int = Query(default=24, ge=1, le=168, description=_HOURS_DESC)
):
    """
    Token usage broken down by provider and model.
    """
    return await get_token_stats(hours=hours)


@router.get("/throughput")
async def metrics_throughput(
    hours: int = Query(default=24, ge=1, le=168, description=_HOURS_DESC)
):
    """
    Requests-per-minute and per-hour time-series with average RPM.
    """
    return await get_throughput_stats(hours=hours)
