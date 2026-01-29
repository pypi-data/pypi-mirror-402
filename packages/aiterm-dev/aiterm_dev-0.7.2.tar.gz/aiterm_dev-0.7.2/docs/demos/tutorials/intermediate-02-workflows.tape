# Tutorial: Intermediate - Steps 5-6: Workflows
# Shows: Workflow commands and chaining

Output intermediate-02-workflows.gif

Set Shell "zsh"
Set FontSize 18
Set Width 900
Set Height 550
Set Theme "Dracula"
Set Padding 15
Set TypingSpeed 40ms

# Title
Type "# Intermediate: Workflow Automation"
Enter
Sleep 1s

# List available workflows
Type "ait workflows list"
Enter
Sleep 3s

# Show a workflow
Type "ait workflows show test"
Enter
Sleep 3s

# Run with dry-run
Type "ait workflows run test --dry-run"
Enter
Sleep 3s

# Chain workflows
Type "ait workflows run lint+test --dry-run"
Enter
Sleep 3s
