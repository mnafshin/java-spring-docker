# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────────────────────
# Variant: ubi9-minimal
# Runtime OS: redhat/ubi9-minimal
# JRE:        custom jlink (glibc – UBI9 is glibc based)
# Notes:      Red Hat Universal Base Image 9 Minimal.
#             Compatible with RHEL/OpenShift environments.
#             Uses microdnf instead of dnf/yum.
#             Long RHEL support lifecycle; suitable for enterprise deployments.
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

# Stage 2 – Custom JRE via jlink (glibc – compatible with UBI9)
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

# Stage 3 – Runtime: redhat/ubi9-minimal
# curl-minimal ships pre-installed on ubi9-minimal; shadow-utils provides
# groupadd/useradd.  We enable the UBI repo explicitly to resolve shadow-utils.
FROM redhat/ubi9-minimal
RUN microdnf install -y --setopt=tsflags=nodocs shadow-utils \
 && microdnf clean all

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
USER 1001
ENTRYPOINT ["java", \
            "-XX:+UseZGC", \
            "-XX:MaxRAMPercentage=75", \
            "-XX:InitialRAMPercentage=50", \
            "-XX:+ExitOnOutOfMemoryError", \
            "-Djava.io.tmpdir=/tmp", \
            "org.springframework.boot.loader.launch.JarLauncher"]

