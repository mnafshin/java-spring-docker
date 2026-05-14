# java-spring-docker

Spring Boot 4 / Java 25 benchmark sandbox with Docker optimization scenarios.

## Dual-tooling workflow

This project supports both Gradle and Maven Wrapper.

### 1) Maven path

```bash
cd /path/to/your-java25-project
./mvnw -DskipTests package
./mvnw test
python3 tools/dockerfile_wizard.py --build-tool maven --profile balanced --output Dockerfile.generated
bash benchmarks/common/run_all_benchmarks.sh --profile quick --build-tool maven
```

### 2) Gradle path

```bash
cd /path/to/your-java25-project
./gradlew build -x test
./gradlew test
python3 tools/dockerfile_wizard.py --build-tool gradle --profile balanced --output Dockerfile.generated
bash benchmarks/common/run_all_benchmarks.sh --profile quick --build-tool gradle
```

### 3) Build-tool regeneration rule for benchmarks

Always pass `--build-tool` to benchmark orchestration so scenario variants are regenerated for the selected build system before execution.

## More docs

- `tools/README.md` for Dockerfile generation profiles and flags.
- `benchmarks/README.md` for benchmark scenarios and run strategy.
- `benchmarks/common/README.md` for runner options and CSV/report workflow.

