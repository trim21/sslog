opinionated logger based on structlog

## development

development dependencies are managed with `uv` and committed in `uv.lock`.

```bash
uv sync --locked --group dev
task typecheck
```

type checking is enforced by [ty](https://github.com/astral-sh/ty) and [pyright](https://microsoft.github.io/pyright/).
