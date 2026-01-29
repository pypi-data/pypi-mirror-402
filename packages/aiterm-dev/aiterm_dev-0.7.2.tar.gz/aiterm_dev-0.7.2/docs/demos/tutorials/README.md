# Tutorial Demo Recordings

VHS tape files for generating tutorial GIF demos.

## Generating GIFs

```bash
# Install VHS (if needed)
brew install charmbracelet/tap/vhs

# Generate single GIF
vhs docs/demos/tutorials/getting-started-01-doctor.tape

# Generate all tutorial GIFs
for tape in docs/demos/tutorials/*.tape; do
  vhs "$tape"
done

# Optimize GIFs (optional)
gifsicle -O3 --colors 256 *.gif -o optimized/
```

## Naming Convention

```
{level}-{step:02d}-{command}.tape
```

Examples:
- `getting-started-01-doctor.tape`
- `intermediate-03-approvals.tape`
- `advanced-07-craft.tape`

## Settings

All tapes use consistent settings:
- Shell: zsh
- Font Size: 18
- Dimensions: 900x550
- Theme: Dracula
- Typing Speed: 40ms
- Padding: 15px
