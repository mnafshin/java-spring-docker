from __future__ import annotations

from springdocker.dockerfile import DockerfileOptions


def render_recipe(options: DockerfileOptions) -> str:
    return "\n".join(
        [
            "# syntax=docker/dockerfile:1",
            f"# custom recipe for {options.build_tool}",
            f"FROM eclipse-temurin:{options.java_version}-jre",
            "WORKDIR /app",
            "COPY app.jar /app/app.jar",
            'ENTRYPOINT ["java","-jar","/app/app.jar"]',
            "",
        ]
    )
