# Git Worktree Workflow

```mermaid
flowchart TD
    subgraph SETUP["One-Time Setup"]
        S1["Create worktree folder"]
        S2["~/.git-worktrees/project/"]
        S1 --> S2
    end

    subgraph CREATE["Create Worktree"]
        C1["git worktree add"]
        C2["Branch: feature/xyz"]
        C3["Path: ~/.git-worktrees/project/feature-xyz"]
        C1 --> C2 --> C3
    end

    subgraph WORK["Parallel Development"]
        W1["Terminal 1: main"]
        W2["Terminal 2: feature"]
        W3["Terminal 3: hotfix"]
        W1 -.-> W2
        W2 -.-> W3
    end

    subgraph FINISH["Complete Feature"]
        F1["Run tests"]
        F2["Update CHANGELOG"]
        F3["Create PR"]
        F4["Merge & cleanup"]
        F1 --> F2 --> F3 --> F4
    end

    SETUP --> CREATE
    CREATE --> WORK
    WORK --> FINISH

    style SETUP fill:#e8f5e9,stroke:#4caf50
    style CREATE fill:#e3f2fd,stroke:#2196f3
    style WORK fill:#fff3e0,stroke:#ff9800
    style FINISH fill:#f3e5f5,stroke:#9c27b0
```

## Commands

```bash
# Setup (once per project)
/craft:git:worktree setup

# Create worktree for feature branch
/craft:git:worktree create feature/new-thing

# List all worktrees
/craft:git:worktree list

# Complete feature (tests + changelog + PR)
/craft:git:worktree finish

# Cleanup merged worktrees
/craft:git:worktree clean
```

## Benefits

- No branch switching needed
- Each terminal stays on its branch
- Uncommitted work stays put
- Perfect for Claude Code sessions
