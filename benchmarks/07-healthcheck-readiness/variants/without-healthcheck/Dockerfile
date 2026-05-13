# syntax=docker/dockerfile:1
# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 – Gradle build
# ──────────────────────────────────────────────────────────────────────────────
FROM eclipse-temurin:25-jdk@sha256:572fe7b5b3ca8beb3b3aca96a7a88f1f7bc98a3bdffd03784a4568962c1a963a AS build
WORKDIR /app

# Copy build descriptors before source so dependency resolution is cached
# independently from source changes.
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
RUN chmod +x gradlew

# Pre-warm the Gradle dependency cache via a BuildKit cache mount so
# dependencies are never re-downloaded (mount is not baked into the image).
RUN --mount=type=cache,sharing=locked,target=/root/.gradle \
    ./gradlew --no-daemon dependencies -q

COPY src ./src
RUN --mount=type=cache,sharing=locked,target=/root/.gradle \
    ./gradlew --no-daemon bootJar -x test --no-build-cache

COPY musthave_modules.txt ./musthave_modules.txt

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2 – Custom JRE (jlink)
# ──────────────────────────────────────────────────────────────────────────────
FROM eclipse-temurin:25-jdk@sha256:572fe7b5b3ca8beb3b3aca96a7a88f1f7bc98a3bdffd03784a4568962c1a963a AS jre-builder

WORKDIR /app_extracted
COPY --from=build /app/build/libs/*-SNAPSHOT.jar app.jar
RUN java -Djarmode=layertools -jar app.jar extract

RUN jdeps \
    --ignore-missing-deps \
    --recursive \
    --multi-release 25 \
    --print-module-deps \
    --class-path 'dependencies/BOOT-INF/lib/*' \
    app.jar > modules.txt

WORKDIR /jre
COPY --from=build /app/musthave_modules.txt ./musthave_modules.txt
RUN set -eux; \
    MODULES=$( (tr ',' '\n' < /app_extracted/modules.txt; cat musthave_modules.txt) \
      | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
      | sort -u \
      | paste -sd, - ); \
    echo "Resolved modules: $MODULES" > modules.used; \
    jlink --add-modules "$MODULES" \
          --strip-debug \
          --no-man-pages \
          --no-header-files \
          --compress=2 \
          --output custom-jre

# ──────────────────────────────────────────────────────────────────────────────
# Stage 3 – JEP 483 AOT cache training run
#
# Runs inside the same OS and custom JRE as the final container so the produced
# cache is bit-for-bit compatible with the production runtime.
# -Dspring.context.exit=onRefresh exits cleanly after all beans are initialised
# (before any port is bound), giving the JVM a chance to record every class that
# application startup touches.
# ──────────────────────────────────────────────────────────────────────────────
FROM debian:bookworm-slim@sha256:d5d3f9c23164ea16f31852f95bd5959aad1c5e854332fe00f7b3a20fcc9f635c AS aot-trainer

COPY --from=jre-builder /jre/custom-jre /opt/java
ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /app
COPY --from=jre-builder /app_extracted/dependencies/ ./
COPY --from=jre-builder /app_extracted/snapshot-dependencies/ ./
COPY --from=jre-builder /app_extracted/spring-boot-loader/ ./
COPY --from=jre-builder /app_extracted/application/ ./

RUN java -XX:AOTCacheOutput=app.aot \
         -Dspring.context.exit=onRefresh \
         org.springframework.boot.loader.launch.JarLauncher; \
    test -f app.aot   # fail the build if the cache was not produced

# ──────────────────────────────────────────────────────────────────────────────
# Stage 4 – Runtime image
# ──────────────────────────────────────────────────────────────────────────────
FROM debian:bookworm-slim@sha256:d5d3f9c23164ea16f31852f95bd5959aad1c5e854332fe00f7b3a20fcc9f635c

# OCI standard image labels – populated via --build-arg in CI:
#   docker build \
#     --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
#     --build-arg GIT_COMMIT=$(git rev-parse --short HEAD) \
#     --build-arg VERSION=1.2.3 ...
ARG BUILD_DATE
ARG GIT_COMMIT
ARG VERSION=0.0.1-SNAPSHOT
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.title="demo-java-spring-docker" \
      org.opencontainers.image.description="Spring Boot 4 / Java 25 – JEP 483 AOT warm container"

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Fixed UID/GID so Kubernetes securityContext.runAsUser can be pinned
# and stays consistent across nodes and image rebuilds.
RUN groupadd --system --gid 1001 javauser \
 && useradd  --system --uid 1001 --gid 1001 \
             --no-create-home --shell /usr/sbin/nologin \
             --comment "java runtime user" javauser

ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Pre-create /app (application files) and /tmp (JVM scratch space) with the
# correct ownership before any files land there.
# In Kubernetes, mount an emptyDir volume at /tmp so writes succeed even with
# readOnlyRootFilesystem: true (see k8s/deployment.yaml).
RUN install -d -o javauser -g javauser -m 755  /app \
 && install -d -o javauser -g javauser -m 1777 /tmp

WORKDIR /app

COPY --from=jre-builder /jre/custom-jre $JAVA_HOME

COPY --from=jre-builder --chown=1001:1001 /app_extracted/dependencies/ ./
COPY --from=jre-builder --chown=1001:1001 /app_extracted/snapshot-dependencies/ ./
COPY --from=jre-builder --chown=1001:1001 /app_extracted/spring-boot-loader/ ./
COPY --from=jre-builder --chown=1001:1001 /app_extracted/application/ ./

# Pre-built JEP 483 AOT class-loading/linking cache (Java 24+).
COPY --from=aot-trainer --chown=1001:1001 /app/app.aot ./app.aot

# 8080 – application traffic
# 8081 – management (actuator health probes + Prometheus metrics)
EXPOSE 8080
EXPOSE 8081

USER 1001

# JVM flags for containerised workloads:
#  -XX:AOTCache                   load JEP 483 class-loading cache (Java 24+)
#  -XX:+UseZGC                    sub-ms GC pauses; ideal for latency-sensitive APIs
#  -XX:MaxRAMPercentage=75        cap heap at 75 % of the cgroup memory limit
#  -XX:InitialRAMPercentage=50    pre-size heap to avoid growth overhead on startup
#  -XX:+ExitOnOutOfMemoryError    crash fast; let Kubernetes restart the pod
#  -Djava.io.tmpdir=/tmp          explicit tmp dir (required with readOnlyRootFilesystem)
#  -Xlog:gc:stdout                GC events to stdout for log aggregators
ENTRYPOINT ["java", \
            "-XX:AOTCache=app.aot", \
            "-XX:+UseZGC", \
            "-XX:MaxRAMPercentage=75", \
            "-XX:InitialRAMPercentage=50", \
            "-XX:+ExitOnOutOfMemoryError", \
            "-Djava.io.tmpdir=/tmp", \
            "-Xlog:gc:stdout", \
            "org.springframework.boot.loader.launch.JarLauncher"]
