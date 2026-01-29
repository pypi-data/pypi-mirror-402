# Complete Git Worktree Workflow Demo
# Shows: Full workflow from create to cleanup

Output worktree-complete.gif

Set Shell "zsh"
Set FontSize 18
Set Width 900
Set Height 550
Set Theme "Dracula"
Set Padding 15
Set TypingSpeed 40ms

# Show current worktrees
Type "# Step 1: Check existing worktrees"
Enter
Sleep 1s
Type "git worktree list"
Enter
Sleep 2.5s

# Create new worktree
Type ""
Enter
Type "# Step 2: Create worktree for new feature"
Enter
Sleep 1s
Type "# mkdir -p ~/.git-worktrees/aiterm"
Enter
Sleep 1s
Type "# git worktree add ~/.git-worktrees/aiterm/new-feature feature/new-feature"
Enter
Sleep 2s

# Show result
Type ""
Enter
Type "# Step 3: Navigate and work"
Enter
Sleep 1s
Type "# cd ~/.git-worktrees/aiterm/new-feature"
Enter
Sleep 1s
Type "# pip install -e ."
Enter
Sleep 1s
Type "# claude  # Start Claude Code in worktree"
Enter
Sleep 2.5s

# Cleanup
Type ""
Enter
Type "# Step 4: After PR merged - cleanup"
Enter
Sleep 1s
Type "# git worktree remove ~/.git-worktrees/aiterm/new-feature"
Enter
Sleep 1s
Type "# git branch -d feature/new-feature"
Enter
Sleep 2s

# Summary
Type ""
Enter
Type "# Summary: Create → Work → Cleanup"
Enter
Sleep 2s

