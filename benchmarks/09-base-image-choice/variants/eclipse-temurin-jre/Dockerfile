# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────────────────────
# Variant: eclipse-temurin-jre
# Runtime OS: eclipse-temurin:25-jre  (Ubuntu-based full JRE, no jlink)
# JRE:        stock JRE (full modules, no stripping)
# Notes:      simplest possible runtime stage; no jlink complexity;
#             larger image than jlink variants.
#             Good baseline to measure jlink benefit.
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

# Stage 2 – Extract layers
FROM eclipse-temurin:25-jdk AS extractor
WORKDIR /app_extracted
COPY --from=build /app/build/libs/*-SNAPSHOT.jar app.jar
RUN java -Djarmode=layertools -jar app.jar extract

# Stage 3 – Runtime: eclipse-temurin:25-jre (full stock JRE)
FROM eclipse-temurin:25-jre

RUN groupadd --system --gid 1001 javauser \
 && useradd --system --uid 1001 --gid 1001 \
            --no-create-home --shell /usr/sbin/nologin javauser
RUN install -d -o javauser -g javauser -m 755 /app \
 && install -d -o javauser -g javauser -m 1777 /tmp
WORKDIR /app
COPY --from=extractor --chown=1001:1001 /app_extracted/dependencies/ ./
COPY --from=extractor --chown=1001:1001 /app_extracted/snapshot-dependencies/ ./
COPY --from=extractor --chown=1001:1001 /app_extracted/spring-boot-loader/ ./
COPY --from=extractor --chown=1001:1001 /app_extracted/application/ ./
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

