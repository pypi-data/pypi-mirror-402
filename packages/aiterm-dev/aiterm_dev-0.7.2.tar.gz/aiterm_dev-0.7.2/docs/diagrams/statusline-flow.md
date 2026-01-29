# StatusLine Flow Diagram

```mermaid
flowchart TB
    Start([Claude Code Session Starts]) --> Init[StatusLine Initialized]
    Init --> Timer[300ms Update Timer]
    
    Timer --> Render[ait statusline render]
    Render --> ReadJSON[Read JSON from stdin]
    
    ReadJSON --> Parse{Parse JSON}
    Parse -->|Success| Extract[Extract Data]
    Parse -->|Error| Fallback[Use Fallback Values]
    
    Extract --> BuildL1[Build Line 1: Project Context]
    Fallback --> BuildL1
    
    BuildL1 --> ProjectSeg[ProjectSegment]
    BuildL1 --> GitSeg[GitSegment]
    
    ProjectSeg --> Icon{Detect Project Type}
    Icon -->|Python| PyIcon[🐍 + venv info]
    Icon -->|R Package| RIcon[📦 + version]
    Icon -->|Node.js| NodeIcon[📦 + version]
    Icon -->|Quarto| QuartoIcon[📊]
    Icon -->|MCP| MCPIcon[🛠️]
    Icon -->|Other| GenIcon[📁]
    
    GitSeg --> GitInfo{Git Repository?}
    GitInfo -->|Yes| GitData[Branch, Status, Worktrees]
    GitInfo -->|No| NoGit[Skip Git Info]
    
    GitData --> Worktree{In Worktree?}
    Worktree -->|Yes| WTMarker[Add (wt) marker]
    Worktree -->|No| WTCount{Multiple Worktrees?}
    WTCount -->|Yes| ShowCount[Show 🌳N]
    WTCount -->|No| NoWT[No worktree display]
    
    PyIcon --> BuildL2
    RIcon --> BuildL2
    NodeIcon --> BuildL2
    QuartoIcon --> BuildL2
    MCPIcon --> BuildL2
    GenIcon --> BuildL2
    NoGit --> BuildL2
    WTMarker --> BuildL2
    ShowCount --> BuildL2
    NoWT --> BuildL2
    
    BuildL2[Build Line 2: Session Info] --> ModelSeg[ModelSegment]
    BuildL2 --> TimeSeg[TimeSegment]
    BuildL2 --> LinesSeg[LinesSegment]
    BuildL2 --> AgentSeg[AgentSegment]
    
    ModelSeg --> ModelName[Shorten Model Name]
    TimeSeg --> TimeIcon{Time of Day}
    TimeIcon -->|6am-12pm| Morning[🌅]
    TimeIcon -->|12pm-6pm| Afternoon[☀️]
    TimeIcon -->|6pm-12am| Evening[🌙]
    TimeIcon -->|12am-6am| Night[🌃]
    
    TimeSeg --> Duration[Session Duration]
    Duration --> Productivity{Idle Time}
    Productivity -->|<5min| Active[🟢]
    Productivity -->|5-15min| Idle[🟡]
    Productivity -->|>15min| LongIdle[🔴]
    
    LinesSeg --> Ghostty{Ghostty Terminal?}
    Ghostty -->|Yes| OSC[Emit OSC 9;4 Progress Bar]
    Ghostty -->|No| NoOSC[Text Only]
    
    OSC --> ProgressType{Lines Changed}
    ProgressType -->|More Added| Success[Green Progress Bar]
    ProgressType -->|More Removed| Error[Red Progress Bar]
    
    AgentSeg --> CheckAgents{Background Agents?}
    CheckAgents -->|Yes| ShowAgents[🤖N]
    CheckAgents -->|No| NoAgents[Skip]
    
    ModelName --> Combine
    Morning --> Combine
    Afternoon --> Combine
    Evening --> Combine
    Night --> Combine
    Active --> Combine
    Idle --> Combine
    LongIdle --> Combine
    Success --> Combine
    Error --> Combine
    NoOSC --> Combine
    ShowAgents --> Combine
    NoAgents --> Combine
    
    Combine[Combine All Segments] --> Format[Apply ANSI Colors]
    Format --> Output[Output 2-Line StatusLine]
    
    Output --> Display[Display in Terminal]
    Display --> Wait[Wait 300ms]
    Wait --> Timer
    
    style Start fill:#e1f5e1
    style Output fill:#fff4e6
    style OSC fill:#e3f2fd
    style Success fill:#c8e6c9
    style Error fill:#ffcdd2
```

## Flow Description

### Initialization

1. Claude Code starts a new session
2. StatusLine is initialized with `ait statusline render` command
3. 300ms update timer begins

### Data Collection (Every 300ms)

1. **JSON Input**: Read project, git, and session data from stdin
2. **Parse**: Extract workspace, model, cost, and style information
3. **Fallback**: Use default values if parsing fails

### Line 1: Project Context

1. **Project Detection**:
   - Check for project type indicators (pyproject.toml, package.json, etc.)
   - Assign appropriate icon (🐍, 📦, 📊, etc.)
   - Detect Python/Node/R environment if enabled

2. **Git Information**:
   - Check if directory is a git repository
   - Extract branch name, dirty status
   - Detect worktree status and count
   - Show ahead/behind, untracked, stash counts

3. **Worktree Display**:
   - If in worktree: Add `(wt)` marker
   - If multiple worktrees exist: Show `🌳N` count

### Line 2: Session Info

1. **Model**: Shorten display name (e.g., "Claude Sonnet 4.5" → "Sonnet 4.5")

2. **Time**:
   - Determine time of day (🌅/☀️/🌙/🌃)
   - Calculate session duration
   - Determine productivity level (🟢/🟡/🔴)

3. **Lines Changed** (Ghostty Enhancement):
   - Check if running in Ghostty terminal
   - If yes: Emit OSC 9;4 escape sequence for native progress bar
   - Green bar: More lines added (success)
   - Red bar: More lines removed (error)

4. **Background Agents**:
   - Check for running Task agents
   - Display count if any active

### Output

1. Combine all segments with proper spacing
2. Apply ANSI color codes based on theme
3. Output 2-line formatted string
4. Display in terminal
5. Wait 300ms and repeat

## Key Features

### Ghostty OSC 9;4 Integration

- **Native Progress Bars**: Ghostty 1.2.x supports graphical progress bars
- **Automatic Detection**: Enabled when `TERM_PROGRAM=ghostty`
- **Visual Feedback**:
  - Lines added > removed = Green success bar
  - Lines removed > added = Red error bar
  - Percentage based on ratio of changes

### Worktree Awareness

- **Multi-branch Workflows**: Shows total worktree count
- **Context Indicator**: `(wt)` marker in non-main worktrees
- **Smart Display**: Only shows when relevant

### Performance

- **Fast Rendering**: <50ms typical render time
- **Cached Data**: Session duration and agent counts cached
- **Efficient Updates**: Only changed segments re-rendered
