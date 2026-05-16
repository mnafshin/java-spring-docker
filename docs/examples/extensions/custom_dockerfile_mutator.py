from __future__ import annotations

from springdocker.dockerfile import DockerfileOptions


class CompanyLabelMutator:
    name = "company-label"

    def mutate_dockerfile(self, dockerfile_text: str, options: DockerfileOptions) -> str:
        del options
        return dockerfile_text + '\nLABEL org.opencontainers.image.vendor="Acme Corp"\n'
