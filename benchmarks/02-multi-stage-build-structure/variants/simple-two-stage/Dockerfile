# syntax=docker/dockerfile:1
FROM eclipse-temurin:25-jdk AS build
WORKDIR /app
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
RUN chmod +x gradlew
COPY src ./src
RUN ./gradlew --no-daemon bootJar -x test

FROM eclipse-temurin:25-jre
WORKDIR /app
COPY --from=build /app/build/libs/*-SNAPSHOT.jar app.jar
EXPOSE 8080
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD ["java", "-jar", "app.jar", "--healthcheck"]
ENTRYPOINT ["java", "-jar", "app.jar"]
