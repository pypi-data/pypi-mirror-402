# Usage Tracking Implementation

## Current Status: Placeholder Implementation

The usage tracking feature is **implemented and ready** but returns empty data because Claude Code does not yet provide a public API for accessing usage limits.

## Architecture

```
UsageTracker (usage.py)
  ├─ get_session_usage() → UsageData | None
  ├─ get_weekly_usage() → UsageData | None
  └─ _parse_claude_usage_command() → (session, weekly)

UsageSegment (segments.py)
  ├─ Uses UsageTracker to get data
  ├─ Formats for display with colors
  └─ Returns empty string if no data available

StatusLineRenderer
  └─ Would call UsageSegment.render() in line2
```

## Integrating Real Data

When Claude Code provides usage tracking, update `UsageTracker` in `usage.py`:

### Option A: CLI Command

If Claude Code adds a `--usage` flag:

```python
def get_session_usage(self) -> Optional[UsageData]:
    """Get current session usage."""
    result = subprocess.run(
        ['claude', '--usage', '--format', 'json'],
        capture_output=True,
        text=True,
        timeout=5
    )

    if result.returncode == 0:
        data = json.loads(result.stdout)
        return UsageData(
            current=data['session']['current'],
            limit=data['session']['limit'],
            reset_time=data['session']['reset_timestamp']
        )

    return None
```

### Option B: Internal Files

If Claude Code writes usage to a file:

```python
def get_session_usage(self) -> Optional[UsageData]:
    """Get current session usage."""
    usage_file = Path.home() / '.claude' / 'usage.json'

    if not usage_file.exists():
        return None

    try:
        with open(usage_file) as f:
            data = json.load(f)

        return UsageData(
            current=data['session']['current'],
            limit=data['session']['limit'],
            reset_time=data['session']['reset_timestamp']
        )
    except Exception:
        return None
```

### Option C: JSON Input

If Claude Code adds usage fields to the JSON input:

```python
# In StatusLineRenderer._build_line2():
usage_data = data.get('usage', {})
session_usage = usage_data.get('session')
weekly_usage = usage_data.get('weekly')

if session_usage:
    usage_segment.set_session_data(UsageData(
        current=session_usage['current'],
        limit=session_usage['limit'],
        reset_time=session_usage['reset_time']
    ))
```

## Display Format

When data is available, the statusLine will show:

```
╰─ Sonnet 4.5 │ 10:30 │ ⏱ 5m │ 📊S:45/100(2h) W:234/500(3d) │ +123/-45
```

Format breakdown:
- `S:45/100(2h)` - Session: 45 of 100 messages, resets in 2 hours
- `W:234/500(3d)` - Weekly: 234 of 500 messages, resets in 3 days

### Color Coding

Usage displays with color based on percentage:
- **Green** (`38;5;2`): < 50% used
- **Yellow** (`38;5;3`): 50-80% used
- **Orange** (`38;5;208`): 80-95% used
- **Red** (`38;5;1`): > 95% used

Threshold is configurable via `usage.warning_threshold` (default: 80).

## Configuration

### Display Control

```bash
# Enable/disable session usage
ait statusline config set display.show_session_usage true

# Enable/disable weekly usage
ait statusline config set display.show_weekly_usage true

# Set warning threshold (percentage)
ait statusline config set usage.warning_threshold 80

# Use compact format
ait statusline config set usage.compact_format true
```

### Config Schema

Already added to `config.py` schema:

```json
{
  "display": {
    "show_session_usage": true,
    "show_weekly_usage": true
  },
  "usage": {
    "show_reset_timer": true,
    "warning_threshold": 80,
    "compact_format": true
  }
}
```

## Testing

### Manual Testing

To test the display with mock data, temporarily modify `UsageTracker.get_session_usage()`:

```python
def get_session_usage(self) -> Optional[UsageData]:
    """Get current session usage."""
    # TESTING: Return mock data
    now = int(datetime.now().timestamp())
    reset_in_2h = now + (2 * 3600)
    return UsageData(
        current=45,
        limit=100,
        reset_time=reset_in_2h
    )
```

Then run:

```bash
ait statusline test
```

### Unit Tests

Run usage tests:

```bash
pytest tests/test_statusline_usage.py -v
```

## Future Enhancements

Once real data is available:

1. **Historical Tracking**: Track usage over time
2. **Alerts**: Warning when approaching limits
3. **Predictions**: Estimate time until limit based on usage rate
4. **Per-Model Limits**: If Claude Code tracks limits per model
5. **Cost Tracking**: If usage includes cost data

## Questions for Claude Code Team

1. Is there a CLI command for usage (`claude --usage`)?
2. Are usage limits stored in a file we can read?
3. Will usage data be added to the JSON input for statusLine?
4. What is the exact format of usage data?
5. Are there separate limits for different model tiers (Sonnet/Opus/Haiku)?

## Developer Notes

- **Why placeholder?** User requested this as #1 priority, but Claude Code API doesn't exist yet
- **Future-proof**: Ready to integrate with real data source
- **Testable**: Can be tested with mock data
- **Configurable**: All display options already in config
- **Documented**: Clear integration path for when API becomes available
