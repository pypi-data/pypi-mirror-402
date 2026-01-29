# aiterm Worktree Setup Demo
# Shows: Creating worktrees with craft and viewing with aiterm

Output worktree-setup.gif

Set Shell "zsh"
Set FontSize 18
Set Width 900
Set Height 550
Set Theme "Dracula"
Set Padding 15
Set TypingSpeed 40ms

# Show current worktrees
Type "git worktree list"
Enter
Sleep 2s

# List features with aiterm
Type "ait feature list"
Enter
Sleep 2.5s

# Show the craft command (demo only)
Type "# Create worktree with craft:"
Enter
Sleep 1s
Type "# /craft:git:worktree create feat/new-feature"
Enter
Sleep 2s

# Show worktree folder structure
Type "ls -la ~/.git-worktrees/"
Enter
Sleep 2.5s
