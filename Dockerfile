FROM gradle:9.2.1-jdk25 AS build
WORKDIR /app
COPY . .
RUN gradle clean build -x test

FROM eclipse-temurin:25-jdk AS jre-builder
WORKDIR /jre

COPY --from=build /app/build/libs/java-spring-docker-0.0.1-SNAPSHOT.jar app.jar
RUN jar xf app.jar

RUN jdeps \
    --ignore-missing-deps \
    --recursive \
    --multi-release 25 \
    --print-module-deps \
    --class-path 'BOOT-INF/lib/*' \
    app.jar > modules.txt

RUN jlink \
    --add-modules $(cat modules.txt) \
    --strip-debug \
    --no-man-pages \
    --no-header-files \
    --compress=2 \
    --output custom-jre


# Running Container

FROM debian:bookworm-slim

ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /app

COPY --from=jre-builder /jre/custom-jre $JAVA_HOME

COPY --from=build /app/build/libs/java-spring-docker-0.0.1-SNAPSHOT.jar app.jar
EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]