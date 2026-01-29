#!/usr/bin/env python3
"""
Canon Keeper Installer

Sets up copilot-instructions.md with the Memory Persistence Protocol.
No MCP server needed - Copilot handles everything directly.

Usage:
    pip install canon-keeper
    python -m canon_keeper install
    
Or:
    python install.py [--workspace /path/to/workspace]
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime


MEMORY_PROTOCOL_DIRECTIVE = '''
### Memory Persistence Protocol (@History) - CRITICAL
**Rule:** When the user includes `@History`, `save this`, `remember this`, or `add to memory` in any message:

1. **Extract Learnings:**
   - Analyze the conversation for technical decisions, architectural choices, workarounds, and insights
   - Format each as: `| Date | Topic | Decision | Rationale |`

2. **Check for Duplicates:**
   - Read the current `copilot-instructions.md` file
   - Compare each new learning against existing entries in the Session Learnings Log
   - Skip any learning that is semantically equivalent to an existing entry

3. **Append New Learnings:**
   - For each non-duplicate learning, append a new row to the Session Learnings Log table
   - Use today's date in YYYY-MM-DD format

4. **Report to User:**
   - Confirm what was saved: "✅ Saved X new learning(s): [topic names]"
   - Report what was skipped: "⏭️ Skipped Y duplicate(s): [topic names]"
   - If nothing new: "No new learnings detected in this conversation."

**Trigger Phrases:** `@History`, `save this`, `remember this`, `add to memory`, `save learning`, `persist this`

**Example:**
```
User: @History save what we learned
Copilot: [analyzes conversation for learnings]
         [reads copilot-instructions.md]
         [checks for duplicates in Session Learnings Log]
         [appends new rows to the table]
         ✅ Saved 2 new learning(s):
           - MCP Config Format
           - Python Venv Path
         ⏭️ Skipped 1 duplicate: Error Handling (already in log)
```
'''


def get_template() -> str:
    """Generate the copilot-instructions.md template."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f'''# Copilot Instructions (Project Memory)

This file serves as persistent memory for GitHub Copilot. It is read at the start of every chat session.

## 1. Project Overview
<!-- Describe your project here -->
- **Project Name:** [Your Project]
- **Description:** [Brief description]
- **Tech Stack:** [Languages, frameworks, libraries]

## 2. Coding Standards
<!-- Define your coding conventions -->
- **Language:** [Primary language]
- **Style Guide:** [Link or description]
- **Naming Conventions:** [camelCase, snake_case, etc.]

## 3. Architecture Decisions
<!-- Document key architectural choices -->
- **Pattern:** [MVC, microservices, etc.]
- **Database:** [Type and rationale]
- **API Style:** [REST, GraphQL, etc.]

## 4. Operational Protocols
<!-- Define how Copilot should behave -->
- **Error Handling:** [Fail fast vs. graceful degradation]
- **Testing:** [Required coverage, test patterns]
- **Documentation:** [Docstring style, README requirements]

## 5. Memory Persistence
{MEMORY_PROTOCOL_DIRECTIVE}

## 6. Session Learnings Log
This section tracks decisions and learnings that evolve over time. Copilot reads this at session start.

| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
| {today} | Canon Keeper Installed | Copilot-based memory persistence | Use @History to save learnings from conversations |

---
*This file was initialized by Canon Keeper. Use `@History` to save learnings from conversations.*
'''


def find_workspace_root(start_path: Path) -> Path:
    """Find workspace root by looking for .git or .vscode folder."""
    current = start_path.resolve()
    
    while current != current.parent:
        if (current / ".git").exists() or (current / ".vscode").exists():
            return current
        current = current.parent
    
    return start_path.resolve()


def setup_copilot_instructions(workspace: Path, force: bool = False) -> bool:
    """Create or update copilot-instructions.md."""
    print("📝 Setting up copilot-instructions.md...")
    
    github_dir = workspace / ".github"
    instructions_file = github_dir / "copilot-instructions.md"
    
    # Ensure .github directory exists
    github_dir.mkdir(exist_ok=True)
    
    if not instructions_file.exists():
        # No file - create full template
        print("   ✅ Creating copilot-instructions.md...")
        instructions_file.write_text(get_template(), encoding="utf-8")
        return True
    
    # File exists - be careful with user's content
    content = instructions_file.read_text(encoding="utf-8")
    
    if "Memory Persistence Protocol" in content:
        print("   ⏭️  Memory Protocol already exists")
        return True
    
    if force:
        # User explicitly wants to overwrite
        print("   🔄 Overwriting with template (--force)...")
        instructions_file.write_text(get_template(), encoding="utf-8")
        return True
    
    # Preserve user's content - just append what's needed
    print("   🔄 Adding Memory Protocol to existing file...")
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if they already have a Session Learnings Log
    has_learnings_log = "Session Learnings Log" in content
    
    # Build the addition
    addition = f'''

---

## Memory Persistence
{MEMORY_PROTOCOL_DIRECTIVE}
'''
    
    if not has_learnings_log:
        addition += f'''
## Session Learnings Log
| Date | Topic | Decision | Rationale |
|------|-------|----------|----------|
| {today} | Canon Keeper Installed | Copilot-based memory persistence | Use @History to save learnings |
'''
    
    addition += '''
---
*Memory persistence added by Canon Keeper.*
'''
    
    # Append to end
    content += addition
    instructions_file.write_text(content, encoding="utf-8")
    print("   ✅ Appended Memory Protocol to existing file")
    print("   💡 Your existing content was preserved")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Install Canon Keeper - Copilot memory persistence"
    )
    parser.add_argument(
        "--workspace", "-w",
        type=Path,
        default=None,
        help="Workspace path (defaults to current directory)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing copilot-instructions.md"
    )
    
    args = parser.parse_args()
    
    # Find workspace
    if args.workspace:
        workspace = args.workspace.resolve()
    else:
        workspace = find_workspace_root(Path.cwd())
    
    print(f"\n🏠 Workspace: {workspace}\n")
    
    # Setup
    success = setup_copilot_instructions(workspace, args.force)
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Canon Keeper installed!")
        print("=" * 50)
        print("\nUsage:")
        print("  In any Copilot chat, say:")
        print('    "@History save what we learned"')
        print('    "save this"')
        print('    "remember this"')
        print("\nCopilot will extract learnings and save them to")
        print(f"  {workspace / '.github' / 'copilot-instructions.md'}")
        print()
        return 0
    else:
        print("\n❌ Installation incomplete")
        return 1


if __name__ == "__main__":
    sys.exit(main())
