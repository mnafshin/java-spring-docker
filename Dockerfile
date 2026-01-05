FROM eclipse-temurin:25-jdk@sha256:572fe7b5b3ca8beb3b3aca96a7a88f1f7bc98a3bdffd03784a4568962c1a963a AS build
WORKDIR /app
COPY . .
RUN chmod +x gradlew
RUN ./gradlew --no-daemon bootJar -x test --no-build-cache

FROM eclipse-temurin:25-jdk@sha256:572fe7b5b3ca8beb3b3aca96a7a88f1f7bc98a3bdffd03784a4568962c1a963a AS jre-builder

WORKDIR /jre

COPY --from=build /app/build/libs/java-spring-docker-*.jar app.jar

RUN java -Djarmode=layertools -jar app.jar extract


RUN jdeps \
    --ignore-missing-deps \
    --recursive \
    --multi-release 25 \
    --print-module-deps \
    --class-path 'dependencies/BOOT-INF/lib/*' \
    app.jar > modules.txt

RUN jlink \
    --add-modules $(cat modules.txt) \
    --strip-debug \
    --no-man-pages \
    --no-header-files \
    --compress=2 \
    --output custom-jre


# Running Container

FROM debian:bookworm-slim@sha256:d5d3f9c23164ea16f31852f95bd5959aad1c5e854332fe00f7b3a20fcc9f635c

RUN mkdir /app
RUN addgroup --system javauser && \
    useradd  --system --no-create-home \
    --gid javauser --shell /usr/sbin/nologin \
    --comment "java user" javauser

ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /app

COPY --from=jre-builder /jre/custom-jre $JAVA_HOME

# COPY --from=build /app/build/libs/java-spring-docker-0.0.1-SNAPSHOT.jar app.jar
COPY --from=jre-builder /jre/dependencies/ ./
COPY --from=jre-builder /jre/snapshot-dependencies/ ./
COPY --from=jre-builder /jre/spring-boot-loader/ ./
COPY --from=jre-builder /jre/application/ ./

EXPOSE 8080

RUN chown -R javauser:javauser /app
USER javauser

# -XX:+UseContainerSupport is enabled by default in Java 10 and later
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-XX:InitialRAMPercentage=50", "-XX:+AlwaysPreTouch", "-XX:+ExitOnOutOfMemoryError", "-Xlog:gc*,safepoint=info", "org.springframework.boot.loader.launch.JarLauncher"]