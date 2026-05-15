# Extension model

`springdocker` does not ship a runtime plugin loader yet. The practical extension model today is to wrap the existing CLI surfaces and reuse the core helpers.

## Extension points

| Surface | Module | Typical customization |
|---|---|---|
| CLI parsing | `src/springdocker/cli.py` | Add new commands or flags. |
| Command orchestration | `src/springdocker/commands.py` | Add validation, extra file I/O, or alternate output formats. |
| Project detection | `src/springdocker/project_detect.py` | Support extra build metadata or repository conventions. |
| Dockerfile generation | `src/springdocker/dockerfile.py` | Post-process generated Dockerfiles or add org-specific defaults. |
| Benchmark reporting | `src/springdocker/analyze.py` | Add new summary columns or renderers. |

## Recommended extension shape

1. Build your project-specific wrapper around the existing helper.
2. Keep the wrapper small and deterministic.
3. Add tests for the wrapper and the underlying helper it depends on.

## Example extension

See `docs/examples/extensions/custom_dockerfile_mutator.py` for a concrete wrapper that adds an organization label after generation.

## Notes

- Prefer a wrapper or adapter over patching generated output by hand.
- If `springdocker` grows a formal plugin API later, keep the wrappers thin so they can migrate without changing the downstream workflow.
