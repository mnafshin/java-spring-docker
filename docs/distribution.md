# Binary distribution

`springdocker` is a Python CLI, so the practical distribution channels are package managers, self-contained launchers, and a containerized runtime.

## Channels

| Channel | Notes |
|---|---|
| `uv tool install springdocker` | Fast Python-native install path for local users. |
| `pipx install springdocker` | Isolated user-scoped CLI install. |
| Homebrew | Suitable for macOS/Linux users who want a tap-based install. |
| Scoop | Good fit for Windows users who prefer manifest-based installs. |
| Standalone binary | Useful when Python should not be installed on the target machine. |
| Dockerized CLI runtime | Good for hermetic CI or one-off invocations. |

## Sample artifacts

See `docs/examples/distribution/` for template files that can be published or adapted:

- `homebrew-formula.rb`
- `scoop-manifest.json`
- `standalone-binary.sh`

## Operational notes

- Keep the published version aligned with `pyproject.toml`.
- Generate release artifacts from tagged builds.
- Prefer the same release process for package managers and standalone assets so the version stays consistent.
