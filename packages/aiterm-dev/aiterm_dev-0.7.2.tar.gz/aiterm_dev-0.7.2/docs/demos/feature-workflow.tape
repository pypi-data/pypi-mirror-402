# aiterm Feature Workflow Demo
# Shows: ait feature status, start, list, cleanup

Output feature-workflow.gif

Set Shell "zsh"
Set FontSize 18
Set Width 900
Set Height 550
Set Theme "Dracula"
Set Padding 15
Set TypingSpeed 40ms

# Show feature status
Type "ait feature status"
Enter
Sleep 3s

# List feature branches
Type "ait feature list"
Enter
Sleep 2.5s

# Start a new feature (demo only - won't actually create)
Type "# Start a feature with worktree:"
Enter
Sleep 1s
Type "# ait feature start my-feature --worktree"
Enter
Sleep 2s

# Show cleanup options
Type "ait feature cleanup --dry-run"
Enter
Sleep 3s
