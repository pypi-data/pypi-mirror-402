# Tutorial: Intermediate - Step 7: Session Management
# Shows: Session tracking and coordination

Output intermediate-03-sessions.gif

Set Shell "zsh"
Set FontSize 18
Set Width 900
Set Height 550
Set Theme "Dracula"
Set Padding 15
Set TypingSpeed 40ms

# Title
Type "# Intermediate: Session Coordination"
Enter
Sleep 1s

# Show active sessions
Type "ait sessions live"
Enter
Sleep 3s

# Show current session
Type "ait sessions current"
Enter
Sleep 2.5s

# Set task for session
Type "ait sessions task 'Working on tutorials'"
Enter
Sleep 2.5s

# Check for conflicts
Type "ait sessions conflicts"
Enter
Sleep 3s
