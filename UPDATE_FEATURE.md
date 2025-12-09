# ✨ DonkeyCar CLI - Update Feature

## New Feature: `donkey system update`

A new update command has been added to the CLI that allows users to easily get the latest version from GitHub.

## What It Does

```bash
donkey system update
```

This command:

1. **Checks for Git** - Validates that git is installed and available
2. **Verifies Repository** - Checks if you're in a valid git repository
3. **Shows Current State** - Displays current branch and git directory
4. **Confirms Update** - Asks for confirmation before proceeding
5. **Fetches Changes** - Runs `git fetch origin`
6. **Checks Out Main** - Switches to the main branch
7. **Pulls Latest** - Gets the latest code with `git pull origin main`
8. **Reinstalls** - Runs `pip install -e .` to update the installation
9. **Confirms Success** - Shows the new version number

## Usage

### Basic Update

```bash
# Update to latest from GitHub
donkey system update

# You'll see output like:
# DonkeyCar Update
# ============================================================
#
# Current Branch: main
# Git Directory: .git
#
# Update DonkeyCar from main branch? [Y/n]: y
#
# Fetching latest changes...
# Checking out main branch...
# Pulling latest changes...
# Reinstalling DonkeyCar...
# ✓ Update complete! Version: 5.2.dev5
```

### If Not in Git Repository

If you're not in a git repository, the command will provide helpful instructions:

```bash
$ donkey system update
DonkeyCar Update
============================================================

✗ Not in a git repository

To update, you need to clone from GitHub:
  git clone https://github.com/autorope/donkeycar.git
  cd donkeycar
  git checkout main
  pip install -e .
```

### If Git Not Installed

If git is not available:

```bash
$ donkey system update
✗ Git not found. Install git to use update command.
```

## Manual Update Alternative

If you prefer to update manually:

```bash
# Navigate to your DonkeyCar directory
cd /path/to/donkeycar

# Fetch latest changes
git fetch origin

# Switch to main branch
git checkout main

# Pull latest code
git pull origin main

# Reinstall
pip install -e .
```

## Requirements

To use `donkey system update`, you need:

- Git installed and in PATH
- A git repository (cloned from GitHub)
- A working Python environment with pip
- Write permissions to the directory

## Error Handling

The command includes robust error handling:

- ✅ Checks for git availability
- ✅ Validates git repository
- ✅ Confirms before making changes
- ✅ Catches subprocess errors
- ✅ Provides helpful fallback instructions
- ✅ Shows current version after update

## When to Use

Use `donkey system update` when:

1. **New features are released** - Get the latest features
2. **Bug fixes are available** - Update to bug-free versions
3. **You want the latest main branch** - Stay current with development
4. **You've cloned from GitHub** - You have a git repository

## When NOT to Use

Don't use `donkey system update` if:

1. **You installed from PyPI** - Use `pip install --upgrade donkeycar` instead
2. **You're not in a git repository** - Clone from GitHub first
3. **You have custom modifications** - Git pull will merge changes (or conflict)
4. **You're on a different branch** - Make sure you're on a compatible branch

## Integration with Other Commands

The update command integrates with other system commands:

```bash
# Check status before updating
donkey system check

# Update to latest
donkey system update

# Verify successful update
donkey system info        # Shows new version
donkey system check       # Confirms all dependencies
```

## Documentation Updates

The update command is now documented in:

1. **donkeycar/cli/README.md**

   - Added to SYSTEM Commands section
   - Includes "Updating the CLI" section with full details
   - Shows both automatic and manual update methods

2. **EXAMPLES.md**

   - Added example of `donkey system update`
   - Shows expected output
   - Included in quick command reference

3. **QUICKSTART.md**
   - Added to command cheat sheet
   - Marked as important system command

## Example Workflow

```bash
# 1. Check your current state
donkey system info
# Shows: DonkeyCar Version: 5.2.dev5

# 2. Check for updates
donkey system check

# 3. Update to latest
donkey system update
# ✓ Update complete! Version: 5.2.dev5 (or newer)

# 4. Verify update
donkey system check
donkey system info
```

## Technical Details

### Implementation

The `update` command is implemented in `donkeycar/cli/commands/system.py`:

```python
@system.command()
def update():
    """Update DonkeyCar to the latest version from GitHub."""
    # 1. Check for git
    # 2. Validate repository
    # 3. Show current state
    # 4. Confirm with user
    # 5. Execute git operations
    # 6. Reinstall with pip
    # 7. Show success message
```

### Dependencies

The command uses:

- `subprocess` - For running git and pip commands
- `click` - For CLI interface
- Python built-ins for validation

No additional dependencies are required.

### Error Handling

```python
try:
    # Run git and pip commands
    subprocess.run(['git', 'fetch', 'origin'], check=True)
    # ... more commands ...
except subprocess.CalledProcessError as e:
    click.secho(f"✗ Update failed: {e}", fg='red')
    # Show recovery instructions
```

## Future Enhancements

Potential improvements for this feature:

- [ ] Check for uncommitted changes before updating
- [ ] Show changelog of updates
- [ ] Option to update to specific branch/tag
- [ ] Rollback capability if update fails
- [ ] Check if PyPI version is newer
- [ ] Update notification system
- [ ] Scheduled automatic updates

## Troubleshooting

### "Git not found"

Install git from https://git-scm.com/

### "Not in a git repository"

Clone from GitHub:

```bash
git clone https://github.com/autorope/donkeycar.git
cd donkeycar
```

### Update fails with conflicts

You might have local changes conflicting with pulled code:

```bash
git status           # See what's different
git stash            # Save your changes
donkey system update # Try again
```

### Version didn't change

Check if you had local changes:

```bash
git log -1           # See latest commit
git status           # See working directory state
```

## Summary

The new `donkey system update` command provides a simple, user-friendly way to keep the CLI up to date with the latest development version from GitHub. It includes robust error handling and helpful messages for common scenarios.

**Usage:**

```bash
donkey system update
```

**That's it!** The CLI will handle the rest. ✨
