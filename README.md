# springdocker mono-repo

Repository layout:

- `src/springdocker/` - installable CLI package.
- `cli/README.md` - CLI usage and configuration docs.
- `samples/java-spring-docker/` - sample Spring Boot Java project (Maven + Gradle) with Docker and benchmark assets.

## Quick start

```bash
cd /path/to/your-repo
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .

# or install globally with pipx
pipx install springdocker
pipx upgrade springdocker

springdocker doctor --project-root samples/java-spring-docker
springdocker init --project-root samples/java-spring-docker --build-tool maven
springdocker benchmark run --project-root samples/java-spring-docker
```

## Sample project docs

- `samples/java-spring-docker/HELP.md`
- `samples/java-spring-docker/tools/README.md`
- `samples/java-spring-docker/benchmarks/README.md`
