# aiterm Session Coordination Demo
# Shows: ait sessions live, current, conflicts, history

Output sessions.gif

Set Shell "zsh"
Set FontSize 18
Set Width 900
Set Height 550
Set Theme "Dracula"
Set Padding 15
Set TypingSpeed 40ms

# Show active sessions
Type "ait sessions live"
Enter
Sleep 3s

# Show current session
Type "ait sessions current"
Enter
Sleep 2.5s

# Check for conflicts
Type "ait sessions conflicts"
Enter
Sleep 2.5s

# Show session history
Type "ait sessions history"
Enter
Sleep 3s

