# syntax=docker/dockerfile:1
# Native image benchmark variant
FROM ghcr.io/graalvm/native-image-community:25 AS build
WORKDIR /app
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
COPY src ./src
RUN chmod +x gradlew && ./gradlew --no-daemon nativeCompile -x test

FROM debian:bookworm-slim
WORKDIR /app

COPY --from=build /app/build/native/nativeCompile/app /app/app
EXPOSE 8080
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 CMD curl -fsS http://localhost:8081/actuator/health/readiness || exit 1
ENTRYPOINT ["/app/app"]

