opinionated logger based on structlog

## development

development dependencies are managed with `uv` and committed in `uv.lock`.

```bash
uv sync --locked --group dev
uv run mypy --show-column-numbers .
```
