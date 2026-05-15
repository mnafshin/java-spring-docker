from __future__ import annotations

from springdocker.dockerfile import DockerfileOptions, build_dockerfile


def build_company_dockerfile() -> str:
    dockerfile = build_dockerfile(
        DockerfileOptions(build_tool="maven", java_version=25, runtime_image="distroless", use_jlink=False)
    )
    return dockerfile + '\nLABEL org.opencontainers.image.vendor="Acme Corp"\n'
