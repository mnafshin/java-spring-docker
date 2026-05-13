# syntax=docker/dockerfile:1
# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 – Gradle build
# ──────────────────────────────────────────────────────────────────────────────
FROM eclipse-temurin:25-jdk@sha256:572fe7b5b3ca8beb3b3aca96a7a88f1f7bc98a3bdffd03784a4568962c1a963a AS build
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
# Stage 3 – Runtime image (no AOT cache)
# ──────────────────────────────────────────────────────────────────────────────
FROM debian:bookworm-slim@sha256:d5d3f9c23164ea16f31852f95bd5959aad1c5e854332fe00f7b3a20fcc9f635c

ARG BUILD_DATE
ARG GIT_COMMIT
ARG VERSION=0.0.1-SNAPSHOT
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.title="demo-java-spring-docker" \
      org.opencontainers.image.description="Spring Boot 4 / Java 25 – Complex AOT cache benchmark (without cache)"


RUN groupadd --system --gid 1001 javauser \
 && useradd  --system --uid 1001 --gid 1001 \
             --no-create-home --shell /usr/sbin/nologin \
             --comment "java runtime user" javauser

ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN install -d -o javauser -g javauser -m 755  /app \
 && install -d -o javauser -g javauser -m 1777 /tmp

WORKDIR /app

COPY --from=jre-builder /jre/custom-jre $JAVA_HOME
COPY --from=jre-builder --chown=1001:1001 /app_extracted/dependencies/ ./
COPY --from=jre-builder --chown=1001:1001 /app_extracted/snapshot-dependencies/ ./
COPY --from=jre-builder --chown=1001:1001 /app_extracted/spring-boot-loader/ ./
COPY --from=jre-builder --chown=1001:1001 /app_extracted/application/ ./

EXPOSE 8080
EXPOSE 8081


USER 1001

# Standard startup without AOT cache - all class loading/linking happens at runtime
ENTRYPOINT ["java", \
            "-XX:+UseZGC", \
            "-XX:MaxRAMPercentage=75", \
            "-XX:InitialRAMPercentage=50", \
            "-XX:+ExitOnOutOfMemoryError", \
            "-Djava.io.tmpdir=/tmp", \
            "-Xlog:gc:stdout", \
            "org.springframework.boot.loader.launch.JarLauncher"]

