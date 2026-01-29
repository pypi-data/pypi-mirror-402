# This is a PyPi package

## Testing

```bash
uv sync --all-groups --all-extras -p 3.14
pytest --testmon
```

## Production

1. Bump the version in `pyproject.toml`
2. Comment out any local path sources in `pyproject.toml` before publishing
3. Run:

```bash
uv lock -U && uv export --frozen --no-editable --no-dev -o requirements.txt > /tmp/uv.txt
rm -rf dist/* && uv build && uv publish --token $PYPI_TOKEN
```
