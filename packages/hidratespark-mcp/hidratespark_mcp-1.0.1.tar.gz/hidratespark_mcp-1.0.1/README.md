# HidrateSpark MCP Server

Model Context Protocol (MCP) server for HidrateSpark smart water bottle API integration.

Track hydration, analyze water intake patterns, and manage your HidrateSpark data directly through Claude Desktop.

## Features

- **Bottle Management**: List registered bottles with battery, capacity, and firmware info
- **Hydration Tracking**: Query water intake by date or date range
- **Daily Summaries**: Get daily totals, goals, and progress percentages
- **Weekly Analytics**: 7-day breakdown with daily averages
- **Manual Logging**: Add manual sip entries for water from other sources
- **Session Caching**: Efficient authentication with in-memory token caching

## Installation

### 1. Clone or Download

```bash
cd ~/Desktop/Projects/04-Personal-Tools
git clone https://github.com/yourusername/hidratespark-mcp.git
cd hidratespark-mcp
```

### 2. Install Package

```bash
pip install -e .
```

Or with uv:

```bash
uvx --from . hidratespark-mcp
```

### 3. Configure Environment Variables

Copy the example configuration:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# API Keys (use provided defaults or extract from APK)
HIDRATE_APP_ID=a5Il6d0n6WWkLQwBzlxvpF5P7PEkUYkX045CRgwM
HIDRATE_CLIENT_KEY=mWasknCNtr9dSQGPwUBWb5u4Ilf8Qkeqkwz9Q4eL

# Your HidrateSpark Account
HIDRATE_EMAIL=your.email@example.com
HIDRATE_PASSWORD=your_password_here
```

### 4. Add to Claude Desktop

**Option A: Global Configuration (available in all projects)**

Edit your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "hidratespark": {
      "command": "python",
      "args": ["-m", "hidratespark_mcp.server"],
      "env": {
        "HIDRATE_APP_ID": "a5Il6d0n6WWkLQwBzlxvpF5P7PEkUYkX045CRgwM",
        "HIDRATE_CLIENT_KEY": "mWasknCNtr9dSQGPwUBWb5u4Ilf8Qkeqkwz9Q4eL",
        "HIDRATE_EMAIL": "your.email@example.com",
        "HIDRATE_PASSWORD": "your_password_here"
      }
    }
  }
}
```

Or with uvx:

```json
{
  "mcpServers": {
    "hidratespark": {
      "command": "uvx",
      "args": ["--from", "/Users/yourusername/Desktop/Projects/04-Personal-Tools/hidratespark-mcp", "hidratespark-mcp"],
      "env": {
        "HIDRATE_APP_ID": "a5Il6d0n6WWkLQwBzlxvpF5P7PEkUYkX045CRgwM",
        "HIDRATE_CLIENT_KEY": "mWasknCNtr9dSQGPwUBWb5u4Ilf8Qkeqkwz9Q4eL",
        "HIDRATE_EMAIL": "your.email@example.com",
        "HIDRATE_PASSWORD": "your_password_here"
      }
    }
  }
}
```

**Option B: Project-Specific Configuration (available only in this project)**

Copy the example config:

```bash
cp .claude/mcp.json.example .claude/mcp.json
```

Edit `.claude/mcp.json` with your credentials and correct Python path.

**Important**: `.claude/mcp.json` is git-ignored to protect your credentials.

---

Restart Claude Desktop.

## Available Tools

### `hidrate_get_bottles`

Get list of registered HidrateSpark bottles.

**Parameters**: None

**Returns**: Array of bottles with name, capacity, battery level, serial number, firmware version, glow settings.

**Example**:
```
Show me my HidrateSpark bottles
```

---

### `hidrate_get_sips`

Get water intake sips for a specific date or date range.

**Parameters**:
- `date` (optional): Specific date in YYYY-MM-DD format
- `start_date` (optional): Range start in YYYY-MM-DD format
- `end_date` (optional): Range end in YYYY-MM-DD format
- `limit` (optional): Max results (default: 100, max: 500)

**Returns**: Array of sips with timestamp, amount (ml), manual/sensor indicator, hydration impact.

**Examples**:
```
How much water did I drink today?
Show me all sips from January 15th
Get my water intake for the last week
```

---

### `hidrate_get_daily_summary`

Get daily hydration summary with totals and progress.

**Parameters**:
- `date` (optional): Date in YYYY-MM-DD format (default: today)

**Returns**: Total ml, goal ml, progress %, hydration score, hourly goals, weather data.

**Examples**:
```
How am I doing on my hydration goal today?
Show yesterday's hydration summary
Did I hit my water goal on January 18th?
```

---

### `hidrate_log_sip`

Log a manual water intake entry.

**Parameters**:
- `amount_ml` (required): Amount in milliliters
- `timestamp` (optional): ISO 8601 timestamp (default: now)

**Returns**: Created sip with ID, amount, timestamp.

**Examples**:
```
Log 250ml of water I just drank
Add a manual entry for 500ml at 2pm today
```

---

### `hidrate_get_weekly_summary`

Get weekly hydration summary with daily breakdown.

**Parameters**:
- `week_offset` (optional): Week offset (0 = this week, -1 = last week, default: 0)

**Returns**: Week start/end dates, total week ml, daily average, daily breakdown with progress %.

**Examples**:
```
Show me this week's hydration stats
How did I do last week?
What's my weekly water intake average?
```

---

### `hidrate_get_profile`

Get user profile information.

**Parameters**: None

**Returns**: Email, username, account creation date, session status.

**Example**:
```
Show my HidrateSpark profile
```

## Available Resources

### `hidrate://today`

Real-time access to today's hydration summary.

**Returns**: Current day total ml, goal ml, progress %.

---

### `hidrate://bottles`

Quick access to registered bottles list.

**Returns**: Array of bottles with name, capacity, battery level.

## Usage Examples

### Daily Tracking

```
User: How much water have I drunk today?
Claude: [uses hidrate_get_daily_summary]

User: Show me all my sips from today
Claude: [uses hidrate_get_sips with date=today]
```

### Weekly Analysis

```
User: How did my hydration look this week?
Claude: [uses hidrate_get_weekly_summary]

User: Compare this week to last week
Claude: [uses hidrate_get_weekly_summary with week_offset=0 and week_offset=-1]
```

### Manual Logging

```
User: I just drank 300ml from a glass
Claude: [uses hidrate_log_sip with amount_ml=300]
```

### Bottle Management

```
User: What's my bottle's battery level?
Claude: [uses hidrate_get_bottles]
```

## How It Works

### API Architecture

HidrateSpark uses Parse Server (Backend-as-a-Service) with REST API:
- **Base URL**: https://www.hidrateapp.com/parse/
- **Authentication**: Email/password login → session token
- **Query Language**: MongoDB-style operators (`$gte`, `$lte`, etc.)

### Session Token Caching

The client implements in-memory session token caching:
1. First API call triggers login
2. Session token stored in memory
3. Subsequent calls reuse token
4. No persistent storage (security best practice)

### Critical Implementation Detail

The API has two timestamp fields:
- `time`: When the sip actually occurred (authoritative)
- `createdAt`: When the sip synced to cloud

**This server correctly filters on `time`** to avoid data inconsistencies when bottles sync late.

## Troubleshooting

### Authentication Errors

```json
{"error": "Invalid username/password"}
```

**Solution**: Verify `HIDRATE_EMAIL` and `HIDRATE_PASSWORD` in your config.

---

### Empty Results

```json
{"count": 0, "sips": []}
```

**Possible causes**:
- No data for requested date
- Bottle hasn't synced recently
- Date format incorrect (use YYYY-MM-DD)

---

### API Keys Changed

If you get 403/unauthorized errors with default keys:

1. Download latest HidrateSpark APK from APKMirror
2. Decompile with apktool: `apktool d hidratespark.apk`
3. Extract keys from `com/hidratespark/hidrate/HidrateApplication.smali`
4. Update `HIDRATE_APP_ID` and `HIDRATE_CLIENT_KEY`

## Development

### Project Structure

```
hidratespark-mcp/
├── hidratespark_mcp/
│   ├── __init__.py       # Package metadata
│   ├── client.py         # HidrateSpark API client
│   └── server.py         # MCP server implementation
├── pyproject.toml        # Project config
├── .env.example          # Config template
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (when implemented)
pytest
```

### Code Quality

```bash
# Format code
black hidratespark_mcp/

# Lint
ruff check hidratespark_mcp/
```

## Reverse Engineering Notes

This server was created by reverse engineering the official HidrateSpark Android app:

1. **APK Decompilation**: Used apktool to extract smali bytecode
2. **Key Extraction**: Found Parse API keys in `HidrateApplication.smali`
3. **Endpoint Discovery**: Parsed Retrofit annotations to map API endpoints
4. **Testing**: Validated all endpoints with real account data

### Extracted API Keys

```java
// From HidrateApplication.smali lines 507-514
Application-Id: a5Il6d0n6WWkLQwBzlxvpF5P7PEkUYkX045CRgwM
Client-Key: mWasknCNtr9dSQGPwUBWb5u4Ilf8Qkeqkwz9Q4eL
```

These keys are embedded in the public Android app and shared across all users.

## Privacy & Security

- **No data storage**: This server doesn't store any hydration data
- **Session tokens**: In-memory only, cleared on server restart
- **Credentials**: Never logged or transmitted beyond Parse API
- **Open source**: All code available for security review

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Acknowledgments

- HidrateSpark LLC for the smart water bottle
- Parse Server for the BaaS platform
- MCP protocol by Anthropic

## Disclaimer

This is an unofficial reverse-engineered client. Not affiliated with or endorsed by HidrateSpark LLC. Use at your own risk. API keys and endpoints may change without notice.
