# Craft Plugin Integration

```mermaid
flowchart TB
    subgraph AITERM["aiterm CLI"]
        A1["ait learn"]
        A2["ait release"]
        A3["ait workflows"]
        A4["ait sessions"]
    end

    subgraph CRAFT["Craft Plugin"]
        B1["/craft:docs:guide"]
        B2["/craft:docs:demo"]
        B3["/craft:docs:mermaid"]
        B4["/craft:git:worktree"]
        B5["/craft:check release"]
        B6["/craft:orchestrate"]
    end

    subgraph WORKFLOW["Workflow Plugin"]
        C1["/workflow:brainstorm"]
        C2["/workflow:done"]
        C3["/workflow:focus"]
    end

    subgraph OUTPUT["Generated Assets"]
        D1["Tutorial Guides"]
        D2["GIF Demos"]
        D3["Mermaid Diagrams"]
        D4["REFCARDs"]
    end

    A1 --> B1
    A1 --> B2
    A1 --> B3

    A2 --> B5

    A3 --> C1
    A3 --> C2

    B1 --> D1
    B2 --> D2
    B3 --> D3
    B1 --> D4

    B4 --> A3
    B6 --> C1

    style AITERM fill:#e8f5e9,stroke:#4caf50
    style CRAFT fill:#e3f2fd,stroke:#2196f3
    style WORKFLOW fill:#fff3e0,stroke:#ff9800
    style OUTPUT fill:#f3e5f5,stroke:#9c27b0
```

## Key Integration Points

| aiterm | craft | Purpose |
|--------|-------|---------|
| `ait learn` | `/craft:docs:guide` | Generate tutorial content |
| `ait learn` | `/craft:docs:demo` | Create GIF recordings |
| `ait release` | `/craft:check release` | Pre-release audit |
| `ait workflows` | `/craft:git:worktree` | Parallel development |
