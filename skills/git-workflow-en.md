# git-workflow

## Description
Git workflow and commit conventions.

## Instructions

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Branch Naming
- `feature/xxx`: New features
- `fix/xxx`: Bug fixes
- `release/x.x.x`: Release branches

### Common Commands
```bash
# Interactive rebase last 3 commits
git rebase -i HEAD~3

# Cherry pick specific commit
git cherry-pick <commit-hash>

# Find who changed a line
git blame -L 10,20 file.py
```
