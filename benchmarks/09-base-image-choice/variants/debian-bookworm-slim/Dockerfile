# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────────────────────
# Variant: debian-bookworm-slim (current production baseline)
# Runtime OS: debian:bookworm-slim
# JRE:        custom jlink (glibc)
# Notes:      smallest Debian-based image; glibc compatible; wide ecosystem
# ─────────────────────────────────────────────────────────────────────────────

# Stage 1 – Build
FROM eclipse-temurin:25-jdk AS build
WORKDIR /app
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
RUN chmod +x gradlew
RUN --mount=type=cache,sharing=locked,target=/root/.gradle \
    ./gradlew --no-daemon dependencies -q
COPY src ./src
RUN --mount=type=cache,sharing=locked,target=/root/.gradle \
    ./gradlew --no-daemon bootJar -x test --no-build-cache
COPY musthave_modules.txt ./musthave_modules.txt

# Stage 2 – Custom JRE via jlink
FROM eclipse-temurin:25-jdk AS jre-builder
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
    jlink --add-modules "$MODULES" \
          --strip-debug --no-man-pages --no-header-files --compress=2 \
          --output custom-jre

# Stage 3 – Runtime: debian:bookworm-slim
FROM debian:bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
RUN groupadd --system --gid 1001 javauser \
 && useradd --system --uid 1001 --gid 1001 \
            --no-create-home --shell /usr/sbin/nologin javauser
ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"
RUN install -d -o javauser -g javauser -m 755 /app \
 && install -d -o javauser -g javauser -m 1777 /tmp
WORKDIR /app
COPY --from=jre-builder /jre/custom-jre $JAVA_HOME
COPY --from=jre-builder --chown=1001:1001 /app_extracted/dependencies/ ./
COPY --from=jre-builder --chown=1001:1001 /app_extracted/snapshot-dependencies/ ./
COPY --from=jre-builder --chown=1001:1001 /app_extracted/spring-boot-loader/ ./
COPY --from=jre-builder --chown=1001:1001 /app_extracted/application/ ./
EXPOSE 8080
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -fsS http://localhost:8081/actuator/health/readiness || exit 1
USER 1001
ENTRYPOINT ["java", \
            "-XX:+UseZGC", \
            "-XX:MaxRAMPercentage=75", \
            "-XX:InitialRAMPercentage=50", \
            "-XX:+ExitOnOutOfMemoryError", \
            "-Djava.io.tmpdir=/tmp", \
            "org.springframework.boot.loader.launch.JarLauncher"]

