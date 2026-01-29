# Getting Started with StatusLine (v0.7.0)

**5-Minute Quick Start Guide**

---

## TL;DR

```bash
# 1. Install
ait statusline install

# 2. Test
ait statusline test

# 3. Customize (pick one)
ait statusline setup          # Guided setup (easiest!)
# OR
ait statusline customize      # Unified menu (all options)

# Done! Restart Claude Code to see it
```

---

## What is StatusLine?

A beautiful 2-line status display for Claude Code that shows:
- Your project name & type
- Git branch & status
- Session info (model, time, duration)
- And more!

**Example output:**
```
╭─ ░▒▓ 🐍 aiterm (py3.11)  main* ⇣2 ▓▒░
╰─ Sonnet 4.5 │ 🌅 10:30 │ ⏱ 5m │ +45/-12
```

---

## Step 1: Install (1 minute)

```bash
ait statusline install
```

This updates your Claude Code settings to use aiterm StatusLine.

**Verify it worked:**
```bash
ait statusline test
```

You should see a colorful 2-line status display!

---

## Step 2: Customize (3 minutes)

### Option A: Guided Setup (Recommended for Beginners)

```bash
ait statusline setup
```

You'll see a friendly menu:
```
1. Customize display options
2. Change color theme
3. Adjust spacing
4. Apply preset
5. View settings
6. Edit raw config

What would you like to do? [1]:
```

**Example:** Pick option `2` to change your theme, then pick a color.

### Option B: Unified Menu (All Options at Once)

```bash
ait statusline customize
```

See all display, theme, and spacing options in one interactive menu.

### Option C: Quick Theme Change

```bash
ait statusline theme list           # See available
ait statusline theme set cool-blues # Pick one
```

---

## Step 3: Enable Hooks (Optional, 2 minutes)

Hooks add automatic behavior based on Claude Code events.

### Popular Hooks

**On-Theme-Change** - Auto-update colors when your terminal theme switches:
```bash
ait statusline hooks add on-theme-change
```

**On-Remote-Session** - Show indicator when using /teleport:
```bash
ait statusline hooks add on-remote-session
```

### View Your Hooks

```bash
ait statusline hooks list --installed
```

---

## Step 4: Start Using It!

Close your Claude Code sessions and open a new one.

You should now see your customized StatusLine!

---

## Common Changes

### Change Theme

```bash
ait statusline setup
→ Pick option 2 (Change theme)
→ Choose your color
```

### Hide/Show Information

```bash
ait statusline setup
→ Pick option 1 (Customize display)
→ Toggle what you want to see
```

### Adjust Spacing

```bash
ait statusline setup
→ Pick option 3 (Adjust spacing)
→ Choose: minimal, standard, or spacious
```

### Reset to Default

```bash
ait statusline install --reset
```

---

## Themes Available

| Name | Style | Best For |
|------|-------|----------|
| **purple-charcoal** | Official | Default, all users |
| **cool-blues** | Professional | Development, serious work |
| **forest-greens** | Natural | Coding marathons, focus |

---

## What Information Can You Show?

✅ **Git**
- Branch name
- Dirty status (*)
- Commits ahead/behind
- Stash count
- Worktree indicators

✅ **Session**
- Model name (Sonnet, Opus, etc.)
- Time of day
- Session duration
- Files changed (+/--)

✅ **Environment**
- Python version
- Project type icon

---

## Keyboard Shortcuts (In Interactive Menus)

- **Arrow keys** - Navigate options
- **Enter** - Select option
- **1-9** - Quick number select
- **Ctrl+C** - Exit without saving

---

## Get Help

```bash
# Show this guide
ait statusline help

# See all options
ait statusline --help

# Run health check
ait statusline doctor

# Detailed settings
ait statusline config list

# Verbose test
ait statusline test --verbose
```

---

## Troubleshooting

### StatusLine not showing?

1. Did you run `ait statusline install`?
2. Restart Claude Code
3. Check with: `ait statusline test`

### Changes not saved?

Make sure you exited the menu with **yes** when asked "Save changes?"

### Want default back?

```bash
ait statusline install --reset
```

---

## Next Steps

📖 **Learn More:**
- Full tutorial: `docs/guides/STATUSLINE-PHASE1-TUTORIAL.md`
- All commands: `ait statusline --help`
- Configuration: `docs/guide/statusline.md`

🔧 **Explore Hooks:**
```bash
ait statusline hooks list          # See all available
ait statusline hooks add [name]    # Add one
ait statusline hooks remove [name] # Remove it
```

🎨 **Create Custom Theme:**
Edit `~/.config/aiterm/statusline.json` directly (advanced)

---

## Questions?

Run `ait statusline setup` and explore! The menu guides you through everything.

**Enjoy your new StatusLine! 🎉**
