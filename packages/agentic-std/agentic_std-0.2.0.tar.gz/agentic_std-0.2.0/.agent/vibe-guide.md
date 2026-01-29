# Vibe Guide

## Visual Language

### CLI Output Colors

- **Success**: `Green` - Command completed successfully
- **Warning**: `Yellow` - Non-critical notices or prompts
- **Error**: `Red` - Failures and critical issues
- **Info**: `Cyan` - Informational output and status updates
- **Muted**: `Gray` - Secondary information, file paths

### Typography (Terminal)

- **Headings/Commands**: Bold text
- **Emphasis**: Italic or underlined
- **Code/Paths**: As-is with backticks in documentation

## Brand Voice

### Tone

> Developer-friendly, concise, and action-oriented. We respect the user's time—every message should be purposeful. Think of it as a helpful tool that stays out of your way.

### Style Guidelines

- **Do**: Use imperative mood ("Initialize project", "Run update")
- **Do**: Keep output minimal and scannable
- **Do**: Provide clear next steps after actions
- **Don't**: Over-explain or add unnecessary verbosity
- **Don't**: Use emoji excessively in CLI output
- **Don't**: Assume the user needs hand-holding

### Specific Scenarios

- **Error Messages**: Clear, actionable. State what went wrong and how to fix it.
  - Example: `Error: .agent/ already exists. Use --force to overwrite.`
- **Success Messages**: Brief and confirming.
  - Example: `✓ Created .agent/ with 4 files.`
- **Prompts**: Direct questions, default to the safest option.
  - Example: `Overwrite existing files? [y/N]`
