# Terminals

**Terminal integration guides for aiterm**

aiterm supports multiple terminal emulators with deep integrations for theme management, profile switching, and automation.

---

## 🖥️ Supported Terminals

### [Ghostty](ghostty.md) ⭐ **Recommended**

Modern, GPU-accelerated terminal with native macOS integration.

**Features:**

- 14 built-in themes
- Profile management
- Ghostty 1.2.x support (titlebar styles, background images)
- Auto-reload configuration
- Native progress bars (OSC 9;4)

**Quick Start:**

```bash
ait ghostty status
ait ghostty theme apply catppuccin-mocha
ait ghostty font set "JetBrains Mono" 14
```

**Learn More:** [Ghostty Complete Guide](ghostty.md) | [Ghostty Tutorial](../tutorials/ghostty-setup.md)

---

### iTerm2

Popular macOS terminal with extensive customization.

**Features:**

- Profile switching
- Tab title management
- Color scheme automation
- Badge support

**Quick Start:**

```bash
ait terminals detect
tm profile <name>  # Switch profile via flow-cli
tm title "My Tab"  # Set tab title
```

**Learn More:** [iTerm2 Integration](../../guide/terminals.md#iterm2)

---

### Apple Terminal

Basic macOS terminal support.

**Features:**

- Tab title management
- Basic profile detection

**Quick Start:**

```bash
ait terminals detect
ait switch  # Apply context-aware profile
```

**Learn More:** [Apple Terminal](../../guide/terminals.md#apple-terminal)

---

## 📊 Feature Comparison

| Feature | Ghostty | iTerm2 | Apple Terminal |
|---------|---------|--------|----------------|
| Theme Management | ✅ Built-in | ✅ Manual | ❌ |
| Profile Switching | ✅ | ✅ | ⚠️ Basic |
| Auto-reload Config | ✅ | ❌ | ❌ |
| Tab Titles | ✅ | ✅ | ✅ |
| Progress Bars | ✅ OSC 9;4 | ❌ | ❌ |
| Background Images | ✅ 1.2.x | ✅ | ❌ |
| Keybind Presets | ✅ | ⚠️ Manual | ❌ |

---

## 🎯 Choose Your Terminal

### Use Ghostty if you want

- Modern, fast terminal
- Easy theme/font management
- Native macOS integration
- Latest features (1.2.x)

### Use iTerm2 if you want

- Mature, stable terminal
- Extensive customization
- Split panes and tmux integration
- Established workflows

### Use Apple Terminal if you

- Prefer built-in tools
- Need basic functionality
- Want minimal setup

---

## 🚀 Getting Started

1. **Detect your terminal:**

   ```bash
   ait terminals detect
   ```

2. **List supported terminals:**

   ```bash
   ait terminals list
   ```

3. **Compare features:**

   ```bash
   ait terminals compare
   ```

4. **Apply context:**

   ```bash
   ait switch
   ```

---

## 📚 More Resources

- **[Help Center](../index.md)** - All help topics
- **[Quick Reference](../quick-reference.md)** - Command cheat sheet
- **[Terminal Support Guide](../../guide/terminals.md)** - Full documentation
