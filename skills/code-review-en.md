# code-review

## Description
Code review guidelines for Python projects.

## Instructions

When reviewing Python code, check for:

### Code Style
- PEP 8 compliance
- Meaningful variable names
- Function length (should be < 50 lines)
- Proper docstrings

### Common Issues
- Mutable default arguments: `def foo(x=[])` is dangerous
- Missing type hints
- Unused imports
- Bare `except:` clauses

### Security
- SQL injection vulnerabilities
- Hardcoded secrets
- Command injection in subprocess calls

### Performance
- O(n²) algorithms that could be O(n)
- Unnecessary list comprehensions
- Missing caching for expensive operations

## Example Review Format

```
File: example.py
Issues:
  - Line 10: Mutable default argument
  - Line 25: Missing error handling
  - Line 40: Could use list comprehension
Suggestions:
  - Add type hints
  - Extract to helper function
```
