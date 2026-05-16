# Extension model

`springdocker` now supports a runtime plugin loader for Dockerfile mutation hooks via Python entry points.

## Extension points

| Surface | Module | Typical customization |
|---|---|---|
| CLI parsing | `src/springdocker/cli.py` | Add new commands or flags. |
| Command orchestration | `src/springdocker/commands.py` | Add validation, extra file I/O, or alternate output formats. |
| Project detection | `src/springdocker/project_detect.py` | Support extra build metadata or repository conventions. |
| Dockerfile generation | `src/springdocker/dockerfile.py` | Post-process generated Dockerfiles or add org-specific defaults. |
| Benchmark reporting | `src/springdocker/analyze.py` | Add new summary columns or renderers. |

## Plugin entry point contract

Use the entry point group:

```text
springdocker.dockerfile_mutators
```

A plugin may be:

1. an object (or class) exposing `mutate_dockerfile(dockerfile_text, options) -> str`
2. a callable `(dockerfile_text, options) -> str`

Plugins are executed in discovery order during `springdocker dockerfile generate`.

## Failure handling

- Plugin failures are isolated per plugin.
- Generation still succeeds using the last valid Dockerfile text.
- Warnings are emitted in CLI output for failed plugins.
- Set `SPRINGDOCKER_DISABLE_PLUGINS=1` to bypass plugin loading.

## Recommended extension shape

1. Keep plugin logic deterministic and side-effect free.
2. Return only Dockerfile text from mutators.
3. Add tests for both successful mutation and failure isolation behavior.

## Example extension

See `docs/examples/extensions/custom_dockerfile_mutator.py` for a concrete mutator example that adds an organization label after generation.

## Notes

- Prefer a plugin mutator or small adapter over patching generated output by hand.
- Keep mutators focused; use wrappers when you need larger workflow changes.
