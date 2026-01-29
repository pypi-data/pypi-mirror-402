#!/usr/bin/env python3
"""
HidrateSpark MCP Server

MCP server for HidrateSpark smart water bottle API integration.
Provides tools for tracking hydration, getting daily summaries, and managing water intake data.
"""

import json
from datetime import datetime, timedelta
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent, Resource
import mcp.server.stdio

from .client import HidrateClient


# Initialize MCP server
app = Server("hidratespark-mcp")

# Initialize HidrateSpark client (lazy auth on first use)
client = HidrateClient()


# ============================================================================
# TOOLS
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="hidrate_get_bottles",
            description="Get list of registered HidrateSpark bottles with details (name, capacity, battery, etc.)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="hidrate_get_sips",
            description="Get water intake sips for a date range. Returns timestamp, amount (ml), liquid type, and sensor data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": "Specific date in YYYY-MM-DD format (gets sips for that day only)"
                    },
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Start date in YYYY-MM-DD format (inclusive)"
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date",
                        "description": "End date in YYYY-MM-DD format (inclusive)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum number of results (default: 100, max: 500)"
                    }
                }
            }
        ),
        Tool(
            name="hidrate_get_daily_summary",
            description="Get daily hydration summary with total ml, goal, progress %, and hydration score.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": "Date in YYYY-MM-DD format (default: today)"
                    }
                }
            }
        ),
        Tool(
            name="hidrate_log_sip",
            description="Log a manual water intake entry (useful for tracking water from other sources).",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount_ml": {
                        "type": "number",
                        "description": "Amount of water in milliliters"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "When the sip occurred (ISO 8601 format, default: now)"
                    }
                },
                "required": ["amount_ml"]
            }
        ),
        Tool(
            name="hidrate_get_weekly_summary",
            description="Get weekly hydration summary with daily breakdown and averages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "week_offset": {
                        "type": "integer",
                        "default": 0,
                        "description": "Week offset (0 = this week, -1 = last week, etc.)"
                    }
                }
            }
        ),
        Tool(
            name="hidrate_get_profile",
            description="Get user profile information (email, hydration goals, preferences).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    try:
        if name == "hidrate_get_bottles":
            bottles = client.get_bottles()

            result = {
                "count": len(bottles),
                "bottles": []
            }

            for bottle in bottles:
                result["bottles"].append({
                    "name": bottle.get("name", "Unnamed"),
                    "capacity_ml": bottle.get("capacity"),
                    "battery_percent": bottle.get("batteryLevel"),
                    "serial_number": bottle.get("serialNumber"),
                    "model": bottle.get("description", {}).get("model"),
                    "firmware_version": f"{bottle.get('firmwareBootloaderVersion', 0)}.{bottle.get('firmwareMinorVersion', 0)}",
                    "glow_settings": bottle.get("bottleSettings", {}).get("glow", {}).get("name"),
                    "last_synced": bottle.get("lastSynced", {}).get("iso")
                })

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "hidrate_get_sips":
            # Handle both single date and date range
            if "date" in arguments:
                # Single date: get sips for that day only
                date = datetime.fromisoformat(arguments["date"])
                start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                # Date range
                start = datetime.fromisoformat(arguments["start_date"]) if "start_date" in arguments else None
                end = datetime.fromisoformat(arguments["end_date"]) if "end_date" in arguments else None

            limit = arguments.get("limit", 100)
            sips = client.get_sips(start_date=start, end_date=end, limit=limit)

            result = {
                "count": len(sips),
                "total_ml": sum(s.get("amount", 0) for s in sips),
                "sips": []
            }

            for sip in sips:
                time_iso = sip.get("time", {}).get("iso", sip.get("createdAt", ""))
                result["sips"].append({
                    "timestamp": time_iso,
                    "amount_ml": sip.get("amount"),
                    "is_manual": not sip.get("bottleSerialNumber"),  # No serial = manual entry
                    "hydration_impact": sip.get("hydrationImpact", 1),
                    "liquid_type_id": sip.get("liquidTypeInfo", {}).get("objectId")
                })

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "hidrate_get_daily_summary":
            date = None
            if "date" in arguments:
                date = datetime.fromisoformat(arguments["date"])

            summary = client.get_daily_summary(date)

            if not summary:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "No data found for specified date"})
                )]

            # Use totalAmount instead of total (bug in API)
            total = summary.get("totalAmount", summary.get("total", 0))
            goal = summary.get("goal", 0)
            progress = (total / goal * 100) if goal > 0 else 0

            result = {
                "date": summary.get("date"),
                "total_ml": total,
                "goal_ml": goal,
                "progress_percent": round(progress, 1),
                "hydration_score": summary.get("hydrationScore", {}).get("hydrationScore"),
                "hourly_goals": summary.get("hourlyGoals", {}),
                "weather": {
                    "temperature_k": summary.get("temperature"),
                    "humidity_percent": summary.get("humidity"),
                    "altitude_m": summary.get("altitude")
                }
            }

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "hidrate_log_sip":
            amount_ml = arguments["amount_ml"]
            timestamp = None
            if "timestamp" in arguments:
                timestamp = datetime.fromisoformat(arguments["timestamp"])

            result = client.log_sip(amount_ml, timestamp)

            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "sip_id": result.get("objectId"),
                    "amount_ml": amount_ml,
                    "timestamp": result.get("createdAt")
                }, indent=2)
            )]

        elif name == "hidrate_get_weekly_summary":
            week_offset = arguments.get("week_offset", 0)

            # Calculate week start/end
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
            week_end = week_start + timedelta(days=6)

            week_data = []
            total_week_ml = 0

            for day_offset in range(7):
                day = week_start + timedelta(days=day_offset)
                summary = client.get_daily_summary(day)

                if summary:
                    total = summary.get("totalAmount", summary.get("total", 0))
                    goal = summary.get("goal", 0)
                else:
                    total = 0
                    goal = 0

                total_week_ml += total

                week_data.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "day_name": day.strftime("%A"),
                    "total_ml": total,
                    "goal_ml": goal,
                    "progress_percent": round((total / goal * 100) if goal > 0 else 0, 1)
                })

            result = {
                "week_start": week_start.strftime("%Y-%m-%d"),
                "week_end": week_end.strftime("%Y-%m-%d"),
                "total_week_ml": total_week_ml,
                "daily_average_ml": round(total_week_ml / 7, 1),
                "days": week_data
            }

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "hidrate_get_profile":
            profile = client.get_user_profile()

            result = {
                "email": profile.get("email"),
                "username": profile.get("username"),
                "created_at": profile.get("createdAt"),
                "session_token_active": bool(client._session_token)
            }

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "arguments": arguments
            }, indent=2)
        )]


# ============================================================================
# RESOURCES
# ============================================================================

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="hidrate://today",
            name="Today's Hydration Summary",
            description="Current day hydration summary with total ml and progress",
            mimeType="application/json"
        ),
        Resource(
            uri="hidrate://bottles",
            name="Registered Bottles",
            description="List of all registered HidrateSpark bottles",
            mimeType="application/json"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""

    if uri == "hidrate://today":
        summary = client.get_daily_summary()
        if summary:
            total = summary.get("totalAmount", summary.get("total", 0))
            goal = summary.get("goal", 0)
            return json.dumps({
                "date": summary.get("date"),
                "total_ml": total,
                "goal_ml": goal,
                "progress_percent": round((total / goal * 100) if goal > 0 else 0, 1)
            }, indent=2)
        else:
            return json.dumps({"error": "No data for today"})

    elif uri == "hidrate://bottles":
        bottles = client.get_bottles()
        return json.dumps([{
            "name": b.get("name"),
            "capacity_ml": b.get("capacity"),
            "battery_percent": b.get("batteryLevel")
        } for b in bottles], indent=2)

    else:
        return json.dumps({"error": f"Unknown resource: {uri}"})


# ============================================================================
# MAIN
# ============================================================================

async def async_main():
    """Run MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Entry point for the MCP server."""
    import asyncio
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
