# Canon Keeper

Copilot memory persistence - teach Copilot to remember learnings across sessions.

**Zero dependencies!** Just an installer that sets up `copilot-instructions.md`.

## Install

```bash
pip install canon-keeper
python -m canon_keeper install
```

Or with pipx (no venv needed):
```bash
pipx run canon-keeper
```

That's it! The installer creates `.github/copilot-instructions.md` with:
- Memory Persistence Protocol (`@History` directive)
- Best practices template
- Session Learnings Log table

## Usage

In any Copilot chat, say:

```
@History save what we learned
save this
remember this
add to memory
```

Copilot will:
1. Extract learnings from the conversation
2. Check for duplicates in the Session Learnings Log
3. Append new learnings to `copilot-instructions.md`
4. Report what was saved/skipped

## How It Works

No MCP server. No API keys. No runtime dependencies.

The installer just creates a `copilot-instructions.md` file with a directive that tells Copilot:
1. When you see `@History`, extract learnings from the conversation
2. Read the existing Session Learnings Log
3. Skip duplicates
4. Append new rows to the table

Copilot does all the work using its built-in capabilities.

## Manual Setup

If you prefer not to use pip, just copy this to `.github/copilot-instructions.md`:

```markdown
### Memory Persistence Protocol (@History) - CRITICAL
**Rule:** When the user includes `@History`, `save this`, `remember this`, or `add to memory`:

1. **Extract Learnings:**
   - Analyze the conversation for technical decisions, architectural choices, workarounds
   - Format each as: `| Date | Topic | Decision | Rationale |`

2. **Check for Duplicates:**
   - Read the current `copilot-instructions.md` file
   - Skip any learning semantically equivalent to an existing entry

3. **Append New Learnings:**
   - For each non-duplicate, append a row to the Session Learnings Log table
   - Use today's date (YYYY-MM-DD format)

4. **Report to User:**
   - "✅ Saved X new learning(s): [topics]"
   - "⏭️ Skipped Y duplicate(s): [topics]"

## Session Learnings Log
| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
```

## Example Session Learnings Log

After a few sessions, your log might look like:

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
| 2026-01-18 | MCP Config Format | Use "servers" key, not "mcpServers" | VS Code MCP expects this format |
| 2026-01-18 | Python Venv | Use absolute paths in configs | ${workspaceFolder} doesn't expand |
| 2026-01-18 | Error Handling | Fail fast with clear messages | Easier debugging |

## Options

```bash
python -m canon_keeper install --workspace /path/to/project  # Specify workspace
python -m canon_keeper install --force                       # Overwrite existing file
```

## License

MIT
