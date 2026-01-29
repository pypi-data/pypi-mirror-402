# aiterm Context Detection Demo
# Shows: ait detect, ait switch, profile changes

Output context-detection.gif

Set Shell "zsh"
Set FontSize 18
Set Width 900
Set Height 550
Set Theme "Dracula"
Set Padding 15
Set TypingSpeed 40ms

# Detect project context
Type "ait detect"
Enter
Sleep 3s

# Show current profile
Type "ait profile show"
Enter
Sleep 2.5s

# Switch to match context
Type "ait switch"
Enter
Sleep 3s

# Show available profiles
Type "ait profile list"
Enter
Sleep 2.5s
