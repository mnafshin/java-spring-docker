FROM eclipse-temurin:25-jdk-alpine-3.23 AS build
WORKDIR /app
COPY . .
RUN ./gradlew clean build

FROM eclipse-temurin:25-jre-alpine-3.23
WORKDIR /app
COPY --from=build /app/build/libs/java-spring-docker-0.0.1-SNAPSHOT.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]