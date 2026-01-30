# flake8-context-manager-scope

A Flake8 plugin that detects when context manager variables are used outside their scope.

## The Problem

This catches bugs where a context manager variable (like a database session) is used after the `with` block has exited:

```python
async with get_async_session() as session:
    result = await session.execute(query)

# BUG: session is closed but still being used!
await session.execute(another_query)  # CMS001 error
```

## Installation

```bash
pip install flake8-context-manager-scope
```

## Usage

The plugin automatically runs with flake8:

```bash
flake8 your_code.py
```

### Configuration

You must configure which context manager functions to track.

**In `pyproject.toml`** (requires `flake8-pyproject`):

```toml
[tool.flake8]
context-manager-scope-functions = "get_async_session,get_sync_session"
```

**In `.flake8` or `setup.cfg`:**

```ini
[flake8]
context-manager-scope-functions = get_async_session,get_sync_session
```

## Error Codes

| Code | Description |
|------|-------------|
| CMS001 | Variable from context manager used outside its scope |

## Example

```python
# This will trigger CMS001
async def bad_example():
    async with get_async_session() as session:
        user = await session.get(User, user_id)

    # Error: session used after context manager exited
    await session.refresh(user)

# This is correct
async def good_example():
    async with get_async_session() as session:
        user = await session.get(User, user_id)
        await session.refresh(user)  # Inside the context manager
```
