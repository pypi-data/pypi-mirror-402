# Usage Tracking - Currently Unavailable

## Current Status: DISABLED

Usage tracking is **not available** because Claude Code does not expose usage limits programmatically.

After thorough investigation (Dec 31, 2025), we found that:
- ✅ OAuth token can be extracted from macOS Keychain
- ❌ The `/api/oauth/usage` endpoint rejects OAuth tokens (401: "OAuth authentication is currently not supported")
- ❌ Claude Code stores no local usage data in `~/.claude/`
- ❌ No CLI command exists to query usage
- ❌ The `/usage` slash command uses internal endpoints not exposed to tools

**Bottom line:** There's no way to programmatically access Claude Code usage limits.

## Why Usage Isn't Showing

Claude Code CLI uses OAuth for authentication, so there's no API key stored in `~/.claude/settings.json`. The Anthropic API usage endpoint (`https://api.anthropic.com/api/oauth/usage`) requires an API key for authentication.

## How to Enable Usage Tracking

### Option 1: Provide Your API Key (Recommended)

If you have an Anthropic API key, you can add it to aiterm's config:

```bash
# Add API key to config
ait statusline config set anthropic.api_key "sk-ant-..."

# Verify usage tracking works
python3 -c "
import sys
sys.path.insert(0, 'src')
from aiterm.statusline.usage import UsageTracker
tracker = UsageTracker()
print('Session:', tracker.get_session_usage())
print('Weekly:', tracker.get_weekly_usage())
"
```

**Where to get an API key:**
1. Go to https://console.anthropic.com/
2. Navigate to API Keys
3. Create a new API key
4. Copy and save it securely

**Note:** This will use your API key to check usage limits. The key is only read locally and never shared.

### Option 2: Wait for Claude Code Support

Claude Code team is working on exposing usage data in the statusLine JSON input. Once available, usage will work automatically without any configuration.

**Tracking issues:**
- [Issue #5621](https://github.com/anthropics/claude-code/issues/5621) - StatusLine should expose API usage/quota
- [Issue #10557](https://github.com/anthropics/claude-code/issues/10557) - Add context usage to JSON

### Option 3: Mock Data for Testing

To test the display with mock data, temporarily modify `src/aiterm/statusline/usage.py`:

```python
def get_session_usage(self) -> Optional[UsageData]:
    """Get current session usage (5-hour limit)."""
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

You should see: `📊S:45/100(2h)` in the statusLine.

## Implementation Details

### What's Already Working

✅ UsageTracker class with API fetching
✅ 60-second caching to avoid API spam
✅ Color-coded display (green/yellow/orange/red)
✅ Compact format: `S:45/100(2h) W:234/500(3d)`
✅ Config controls: `display.show_session_usage`, `display.show_weekly_usage`
✅ Integrated into statusLine renderer

### What's Missing

❌ API key access from Claude Code session
❌ OAuth token extraction from Claude Code
❌ Usage data in Claude Code JSON input

### How It Works (When Configured)

1. **Fetch**: Calls `https://api.anthropic.com/api/oauth/usage`
2. **Parse**: Extracts `five_hour` and `seven_day` data
3. **Cache**: Saves to `~/.cache/aiterm/usage.json` (60s TTL)
4. **Format**: Renders as `S:X/Y(time) W:X/Y(time)`
5. **Color**: Based on percentage used (configurable threshold)

## Display Example

When working (with API key configured):

```
╰─ Sonnet 4.5 │ 11:10 🌅 │ ⏱ 1h26m │ 📊S:45/100(2h) W:234/500(3d) │ +123/-45
```

Color coding:
- 🟢 **Green** (< 50%): `S:25/100(4h)`
- 🟡 **Yellow** (50-80%): `S:65/100(1h)`
- 🟠 **Orange** (80-95%): `S:85/100(30m)`
- 🔴 **Red** (> 95%): `S:98/100(15m)`

## Configuration

```bash
# View current usage settings
ait statusline config list | grep -E "(usage|show_session|show_weekly)"

# Toggle session usage display
ait statusline config set display.show_session_usage true

# Toggle weekly usage display
ait statusline config set display.show_weekly_usage true

# Change warning threshold (default: 80%)
ait statusline config set usage.warning_threshold 75

# Use verbose format instead of compact
ait statusline config set usage.compact_format false
```

## Troubleshooting

### "Usage not showing"

1. Check if API key is configured:
   ```bash
   ait statusline config get anthropic.api_key
   ```

2. Test API access:
   ```bash
   python3 -c "
   import sys
   sys.path.insert(0, 'src')
   from aiterm.statusline.usage import UsageTracker
   tracker = UsageTracker()
   print('API Key:', tracker._api_key[:20] + '...' if tracker._api_key else 'None')
   print('Session:', tracker.get_session_usage())
   "
   ```

3. Check cache file:
   ```bash
   cat ~/.cache/aiterm/usage.json | jq
   ```

### "API request failing"

- Verify API key is valid
- Check internet connection
- Look for rate limiting (60s cache helps)
- Check API status: https://status.anthropic.com/

## Future Enhancements

When Claude Code exposes usage data:

1. Remove API key requirement
2. Use JSON input directly
3. Add real-time updates (current: 60s cache)
4. Add historical tracking
5. Add usage predictions
6. Add per-model limits (if available)

## Questions?

See:
- [USAGE-TRACKING-README.md](./USAGE-TRACKING-README.md) - Implementation details
- [Claude Code Docs](https://code.claude.com/docs/en/statusline) - Official statusLine docs
- [GitHub Issues](https://github.com/anthropics/claude-code/issues) - Feature requests
