# syntax=docker/dockerfile:1
# JVM baseline for native-vs-jvm benchmark
FROM eclipse-temurin:25-jdk AS build
WORKDIR /app
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
RUN chmod +x gradlew
COPY src ./src
RUN --mount=type=cache,sharing=locked,target=/root/.gradle ./gradlew --no-daemon bootJar -x test --no-build-cache

FROM eclipse-temurin:25-jre
WORKDIR /app

COPY --from=build /app/build/libs/*-SNAPSHOT.jar app.jar
EXPOSE 8080
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 CMD curl -fsS http://localhost:8081/actuator/health/readiness || exit 1
ENTRYPOINT ["java", "-XX:+UseZGC", "-XX:MaxRAMPercentage=75", "-XX:InitialRAMPercentage=50", "-XX:+ExitOnOutOfMemoryError", "-Djava.io.tmpdir=/tmp", "-jar", "app.jar"]

