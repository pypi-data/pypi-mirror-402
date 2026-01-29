# AsyncCacheTools

A wrapper over cachetools for use with asynchronous functions.

## Installation

```bash
pip install asynccachetools
```

## Usage

```python
from asynccachetools import acached
from cachetools import TTLCache
import asyncio

cache = TTLCache(maxsize=100, ttl=300)

@acached(cache=cache)
async def expensive_function(arg1, arg2):
    # Your async function here
    return result
```

## Development

### Building the package

```bash
# Build distribution packages
poetry build
```

This will create `.whl` and `.tar.gz` files in the `dist/` directory.

### Publishing to PyPI

1. **Configure PyPI credentials** (first time only):
   ```bash
   poetry config pypi-token.pypi your-pypi-token
   ```
   Or use username/password:
   ```bash
   poetry config http-basic.pypi your-username your-password
   ```

2. **Update version** in `pyproject.toml` if needed:
   ```toml
   version = "0.1.8"
   ```

3. **Publish to PyPI**:
   ```bash
   poetry publish
   ```

   Or publish to Test PyPI first:
   ```bash
   poetry publish --repository testpypi
   ```

### Local development setup

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linter
poetry run flake8
```

