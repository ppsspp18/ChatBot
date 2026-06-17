from datetime import datetime, timedelta
from typing import Optional
import math

from app.database.mongodb import inference_logs_collection, conversations_collection


# ── helpers ──────────────────────────────────────────────────────────────────

def _time_filter(hours: int) -> dict:
    since = datetime.utcnow() - timedelta(hours=hours)
    return {"created_at": {"$gte": since}}


# ── overview ─────────────────────────────────────────────────────────────────

async def get_overview(hours: int = 24) -> dict:
    """
    Total calls, tokens, errors, avg latency for the last N hours.
    """
    match = {"$match": _time_filter(hours)}

    pipeline = [
        match,
        {
            "$group": {
                "_id": None,
                "total_calls":        {"$sum": 1},
                "total_prompt_tokens":{"$sum": "$prompt_tokens"},
                "total_completion_tokens": {"$sum": "$completion_tokens"},
                "total_tokens":       {"$sum": "$total_tokens"},
                "avg_latency_ms":     {"$avg": "$latency_ms"},
                "error_count": {
                    "$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
                },
                "success_count": {
                    "$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                },
            }
        },
    ]

    result = await inference_logs_collection.aggregate(pipeline).to_list(1)

    if not result:
        return {
            "total_calls": 0,
            "total_tokens": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "avg_latency_ms": 0.0,
            "error_count": 0,
            "success_count": 0,
            "error_rate": 0.0,
            "window_hours": hours,
        }

    row = result[0]
    total = row["total_calls"]
    row.pop("_id", None)
    row["error_rate"] = round(row["error_count"] / total * 100, 2) if total else 0.0
    row["avg_latency_ms"] = round(row["avg_latency_ms"] or 0.0, 2)
    row["window_hours"] = hours
    return row


# ── latency ──────────────────────────────────────────────────────────────────

async def get_latency_stats(hours: int = 24) -> dict:
    """
    p50 / p95 / p99 latency + hourly time-series buckets.
    MongoDB $percentile requires v7+; we compute manually for M0 compatibility.
    """
    match = _time_filter(hours)

    # Fetch all latency values in the window (sorted ascending)
    cursor = inference_logs_collection.find(
        match, {"latency_ms": 1, "created_at": 1, "_id": 0}
    ).sort("latency_ms", 1)

    docs = await cursor.to_list(length=10_000)
    latencies = [d["latency_ms"] for d in docs if d.get("latency_ms") is not None]

    def percentile(sorted_list, pct):
        if not sorted_list:
            return 0.0
        idx = math.ceil(pct / 100 * len(sorted_list)) - 1
        return round(sorted_list[max(0, idx)], 2)

    p50  = percentile(latencies, 50)
    p95  = percentile(latencies, 95)
    p99  = percentile(latencies, 99)
    avg  = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    mn   = round(latencies[0], 2) if latencies else 0.0
    mx   = round(latencies[-1], 2) if latencies else 0.0

    # Hourly time-series
    pipeline_ts = [
        {"$match": match},
        {
            "$group": {
                "_id": {
                    "year":  {"$year":  "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day":   {"$dayOfMonth": "$created_at"},
                    "hour":  {"$hour":  "$created_at"},
                },
                "avg_latency_ms": {"$avg": "$latency_ms"},
                "count":          {"$sum": 1},
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1, "_id.hour": 1}},
    ]

    ts_docs = await inference_logs_collection.aggregate(pipeline_ts).to_list(1000)
    time_series = []
    for doc in ts_docs:
        g = doc["_id"]
        ts = f"{g['year']:04d}-{g['month']:02d}-{g['day']:02d} {g['hour']:02d}:00"
        time_series.append({
            "timestamp":     ts,
            "avg_latency_ms": round(doc["avg_latency_ms"] or 0.0, 2),
            "count":          doc["count"],
        })

    return {
        "p50_ms":      p50,
        "p95_ms":      p95,
        "p99_ms":      p99,
        "avg_ms":      avg,
        "min_ms":      mn,
        "max_ms":      mx,
        "sample_count": len(latencies),
        "time_series": time_series,
        "window_hours": hours,
    }


# ── errors ───────────────────────────────────────────────────────────────────

async def get_error_stats(hours: int = 24) -> dict:
    """
    Error counts broken down by error_message type and by provider.
    """
    match = {"$match": {**_time_filter(hours), "status": "error"}}

    # By provider
    by_provider = await inference_logs_collection.aggregate([
        match,
        {"$group": {"_id": "$provider", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]).to_list(100)

    # By error message category (first 80 chars as key)
    by_type = await inference_logs_collection.aggregate([
        match,
        {
            "$group": {
                "_id": {
                    "$ifNull": [
                        {"$substr": ["$error_message", 0, 80]},
                        "unknown",
                    ]
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 20},
    ]).to_list(20)

    # Hourly error rate time-series
    ts_pipeline = [
        {"$match": _time_filter(hours)},
        {
            "$group": {
                "_id": {
                    "year":  {"$year":  "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day":   {"$dayOfMonth": "$created_at"},
                    "hour":  {"$hour":  "$created_at"},
                },
                "total":  {"$sum": 1},
                "errors": {
                    "$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
                },
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1, "_id.hour": 1}},
    ]
    ts_docs = await inference_logs_collection.aggregate(ts_pipeline).to_list(1000)
    time_series = []
    for doc in ts_docs:
        g = doc["_id"]
        ts = f"{g['year']:04d}-{g['month']:02d}-{g['day']:02d} {g['hour']:02d}:00"
        total = doc["total"]
        errors = doc["errors"]
        time_series.append({
            "timestamp":  ts,
            "total":      total,
            "errors":     errors,
            "error_rate": round(errors / total * 100, 2) if total else 0.0,
        })

    return {
        "by_provider":  [{"provider": d["_id"], "count": d["count"]} for d in by_provider],
        "by_type":      [{"error_type": d["_id"], "count": d["count"]} for d in by_type],
        "time_series":  time_series,
        "window_hours": hours,
    }


# ── tokens ───────────────────────────────────────────────────────────────────

async def get_token_stats(hours: int = 24) -> dict:
    """
    Token usage broken down by provider and model, with daily time-series.
    """
    match = _time_filter(hours)

    by_provider = await inference_logs_collection.aggregate([
        {"$match": match},
        {
            "$group": {
                "_id": "$provider",
                "prompt_tokens":     {"$sum": "$prompt_tokens"},
                "completion_tokens": {"$sum": "$completion_tokens"},
                "total_tokens":      {"$sum": {"$add": [
                    "$prompt_tokens",
                    "$completion_tokens"
                ]}},
                "call_count":        {"$sum": 1},
            }
        },
        {"$sort": {"total_tokens": -1}},
    ]).to_list(50)

    by_model = await inference_logs_collection.aggregate([
        {"$match": match},
        {
            "$group": {
                "_id": {"provider": "$provider", "model": "$model"},
                "total_tokens": {"$sum": {"$add": [
                    "$prompt_tokens",
                    "$completion_tokens"
                ]}},
                "call_count":   {"$sum": 1},
            }
        },
        {"$sort": {"total_tokens": -1}},
        {"$limit": 20},
    ]).to_list(20)

    return {
        "by_provider": [
            {
                "provider":          d["_id"],
                "prompt_tokens":     d["prompt_tokens"],
                "completion_tokens": d["completion_tokens"],
                "total_tokens":      d["total_tokens"],
                "call_count":        d["call_count"],
            }
            for d in by_provider
        ],
        "by_model": [
            {
                "provider":     d["_id"]["provider"],
                "model":        d["_id"]["model"],
                "total_tokens": d["total_tokens"],
                "call_count":   d["call_count"],
            }
            for d in by_model
        ],
        "window_hours": hours,
    }


# ── throughput ───────────────────────────────────────────────────────────────

async def get_throughput_stats(hours: int = 24) -> dict:
    """
    Requests-per-minute / per-hour time series.
    """
    match = _time_filter(hours)

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": {
                    "year":   {"$year":  "$created_at"},
                    "month":  {"$month": "$created_at"},
                    "day":    {"$dayOfMonth": "$created_at"},
                    "hour":   {"$hour":  "$created_at"},
                    "minute": {"$minute": "$created_at"},
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {
            "_id.year": 1, "_id.month": 1, "_id.day": 1,
            "_id.hour": 1, "_id.minute": 1,
        }},
    ]

    docs = await inference_logs_collection.aggregate(pipeline).to_list(10_000)

    per_minute = []
    for doc in docs:
        g = doc["_id"]
        ts = (
            f"{g['year']:04d}-{g['month']:02d}-{g['day']:02d} "
            f"{g['hour']:02d}:{g['minute']:02d}"
        )
        per_minute.append({"timestamp": ts, "requests": doc["count"]})

    # Also aggregate to hourly for longer windows
    hourly: dict = {}
    for item in per_minute:
        hour_key = item["timestamp"][:13]   # "YYYY-MM-DD HH"
        hourly[hour_key] = hourly.get(hour_key, 0) + item["requests"]

    per_hour = [
        {"timestamp": k + ":00", "requests": v}
        for k, v in sorted(hourly.items())
    ]

    total = sum(d["requests"] for d in per_minute)
    minutes_elapsed = max(len(per_minute), 1)
    avg_rpm = round(total / minutes_elapsed, 2)

    return {
        "per_minute":   per_minute[-60:],   # last 60 data points
        "per_hour":     per_hour,
        "avg_rpm":      avg_rpm,
        "total_requests": total,
        "window_hours": hours,
    }
