# Multi-architecture builds

`springdocker` generated Dockerfiles are Buildx-friendly by default.

## What is generated

- `ARG TARGETPLATFORM`
- `ARG BUILDPLATFORM`
- build stages pinned to `--platform=$BUILDPLATFORM`
- runtime stages pinned to `--platform=$TARGETPLATFORM`

This keeps the same Dockerfile usable for `linux/amd64` and `linux/arm64` builds.

## Example build command

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t app:multiarch .
```

## Notes

- The base images used by the sample generator are multi-arch tags.
- Distroless and Temurin runtime variants both remain compatible with the generated buildx flow.
