FROM eclipse-temurin:25-jdk@sha256:572fe7b5b3ca8beb3b3aca96a7a88f1f7bc98a3bdffd03784a4568962c1a963a AS build
WORKDIR /app

# Copy wrapper/build files first so dependency resolution stays cached when only source changes.
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
RUN chmod +x gradlew

COPY src ./src
RUN ./gradlew --no-daemon bootJar -x test --no-build-cache

# Keep this out of the bootJar cache path; it only affects the jlink stage.
COPY musthave_modules.txt ./musthave_modules.txt

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

# include repo "must-have" modules and dedupe/sort with jdeps output
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


# AOT cache training stage — runs inside the same OS and custom JRE as the final container
# so the generated cache is bit-for-bit compatible with the production runtime.
# -Dspring.context.exit=onRefresh causes Spring Boot 4 to exit cleanly after all beans
# are loaded (before binding a port), giving the JVM a chance to record every class that
# application startup touches.

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


# Running Container

FROM debian:bookworm-slim@sha256:d5d3f9c23164ea16f31852f95bd5959aad1c5e854332fe00f7b3a20fcc9f635c

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN addgroup --system javauser && \
    useradd  --system --no-create-home \
    --gid javauser --shell /usr/sbin/nologin \
    --comment "java user" javauser

ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /app

COPY --from=jre-builder /jre/custom-jre $JAVA_HOME

COPY --from=jre-builder --chown=javauser:javauser /app_extracted/dependencies/ ./
COPY --from=jre-builder --chown=javauser:javauser /app_extracted/snapshot-dependencies/ ./
COPY --from=jre-builder --chown=javauser:javauser /app_extracted/spring-boot-loader/ ./
COPY --from=jre-builder --chown=javauser:javauser /app_extracted/application/ ./

# Embed the pre-built AOT class-loading cache so the JVM can skip class loading/linking on startup.
COPY --from=aot-trainer --chown=javauser:javauser /app/app.aot ./app.aot

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -fsS http://localhost:8080/actuator/health/readiness || exit 1

USER javauser

# -XX:+UseContainerSupport is enabled by default in Java 10 and later
# -XX:AOTCache loads the pre-built class loading/linking cache (JEP 483, Java 24+)
ENTRYPOINT ["java", \
            "-XX:AOTCache=app.aot", \
            "-XX:MaxRAMPercentage=75", \
            "-XX:InitialRAMPercentage=50", \
            "-XX:+AlwaysPreTouch", \
            "-XX:+ExitOnOutOfMemoryError", \
            "-Xlog:gc*,safepoint=info", \
            "org.springframework.boot.loader.launch.JarLauncher"]
