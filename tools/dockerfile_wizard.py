#!/usr/bin/env python3
"""Interactive Dockerfile wizard for this Spring Boot project.

Generates a Dockerfile based on runtime requirements discovered in benchmarks.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WizardConfig:
    runtime_base: str
    use_buildkit_cache: bool
    use_jlink: bool
    use_aot_cache: bool
    non_root: bool
    healthcheck: bool
    tuned_jvm_flags: bool
    pin_digests: bool
    use_native_image: bool
    output: Path


PROFILES: dict[str, dict[str, object]] = {
    "balanced": {
        "runtime_base": "debian-bookworm-slim",
        "use_buildkit_cache": True,
        "use_jlink": True,
        "use_aot_cache": False,
        "non_root": True,
        "healthcheck": True,
        "tuned_jvm_flags": True,
        "pin_digests": False,
    },
    "smallest": {
        "runtime_base": "alpine",
        "use_buildkit_cache": True,
        "use_jlink": True,
        "use_aot_cache": False,
        "non_root": True,
        "healthcheck": True,
        "tuned_jvm_flags": True,
        "pin_digests": False,
    },
    "enterprise": {
        "runtime_base": "ubi9-minimal",
        "use_buildkit_cache": True,
        "use_jlink": True,
        "use_aot_cache": False,
        "non_root": True,
        "healthcheck": True,
        "tuned_jvm_flags": True,
        "pin_digests": False,
    },
    "simplest": {
        "runtime_base": "eclipse-temurin-jre",
        "use_buildkit_cache": True,
        "use_jlink": False,
        "use_aot_cache": False,
        "non_root": True,
        "healthcheck": True,
        "tuned_jvm_flags": True,
        "pin_digests": False,
    },
    "coldstart": {
        "runtime_base": "debian-bookworm-slim",
        "use_buildkit_cache": True,
        "use_jlink": True,
        "use_aot_cache": True,
        "non_root": True,
        "healthcheck": True,
        "tuned_jvm_flags": True,
        "pin_digests": False,
        "use_native_image": False,
    },
    "native": {
        "runtime_base": "debian-bookworm-slim",
        "use_buildkit_cache": True,
        "use_jlink": False,
        "use_aot_cache": False,
        "non_root": True,
        "healthcheck": True,
        "tuned_jvm_flags": False,
        "pin_digests": False,
        "use_native_image": True,
    },
}


def ask_choice(prompt: str, options: list[str], default_index: int) -> str:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, start=1):
        marker = " (default)" if i == default_index else ""
        print(f"  {i}) {opt}{marker}")
    raw = input("> ").strip()
    if not raw:
        return options[default_index - 1]
    if raw.isdigit() and 1 <= int(raw) <= len(options):
        return options[int(raw) - 1]
    print("Invalid choice, using default.")
    return options[default_index - 1]


def ask_bool(prompt: str, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    raw = input(f"\n{prompt} {suffix} ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes"}


def runtime_settings(runtime_base: str, pin_digests: bool) -> dict[str, str]:
    build_jdk = "eclipse-temurin:25-jdk"
    if pin_digests:
        build_jdk = "eclipse-temurin:25-jdk@sha256:572fe7b5b3ca8beb3b3aca96a7a88f1f7bc98a3bdffd03784a4568962c1a963a"

    base_map = {
        "debian-bookworm-slim": "debian:bookworm-slim",
        "ubuntu-noble": "ubuntu:24.04",
        "alpine": "alpine:3.21",
        "ubi9-minimal": "redhat/ubi9-minimal",
        "eclipse-temurin-jre": "eclipse-temurin:25-jre",
    }
    runtime = base_map[runtime_base]
    if pin_digests and runtime_base == "debian-bookworm-slim":
        runtime = "debian:bookworm-slim@sha256:d5d3f9c23164ea16f31852f95bd5959aad1c5e854332fe00f7b3a20fcc9f635c"

    return {
        "build_jdk": build_jdk,
        "jlink_jdk": "eclipse-temurin:25-jdk-alpine" if runtime_base == "alpine" else build_jdk,
        "runtime": runtime,
    }


def install_block(runtime_base: str, need_user_tools: bool) -> str:
    if runtime_base == "alpine":
        pkgs = ["curl"]
        if need_user_tools:
            pkgs.append("shadow")
        return "RUN apk add --no-cache " + " ".join(pkgs)
    if runtime_base == "ubi9-minimal":
        pkgs = []
        if need_user_tools:
            pkgs.append("shadow-utils")
        if not pkgs:
            return "RUN true"
        return "RUN microdnf install -y --setopt=tsflags=nodocs " + " ".join(pkgs) + " && microdnf clean all"
    pkgs = ["curl"]
    if need_user_tools:
        pkgs.append("passwd")
    return "RUN apt-get update && apt-get install -y --no-install-recommends " + " ".join(pkgs) + " && rm -rf /var/lib/apt/lists/*"


def build_dockerfile(cfg: WizardConfig) -> str:
    if cfg.use_native_image:
        return build_native_dockerfile(cfg)

    if cfg.runtime_base == "eclipse-temurin-jre":
        cfg.use_jlink = False

    if cfg.use_aot_cache and not cfg.use_jlink:
        # Keep wizard safe and predictable.
        cfg.use_aot_cache = False

    s = runtime_settings(cfg.runtime_base, cfg.pin_digests)
    build_jdk = s["build_jdk"]
    jlink_jdk = s["jlink_jdk"]
    runtime = s["runtime"]

    lines: list[str] = []
    lines.append("# syntax=docker/dockerfile:1")
    lines.append("# Generated by tools/dockerfile_wizard.py")
    lines.append("")

    # Build stage
    lines.append(f"FROM {build_jdk} AS build")
    lines.append("WORKDIR /app")
    lines.append("COPY gradlew build.gradle settings.gradle ./")
    lines.append("COPY gradle ./gradle")
    lines.append("RUN chmod +x gradlew")
    if cfg.use_buildkit_cache:
        lines.append("RUN --mount=type=cache,sharing=locked,target=/root/.gradle \\")
        lines.append("    ./gradlew --no-daemon dependencies -q")
    else:
        lines.append("RUN ./gradlew --no-daemon dependencies -q")
    lines.append("COPY src ./src")
    if cfg.use_buildkit_cache:
        lines.append("RUN --mount=type=cache,sharing=locked,target=/root/.gradle \\")
        lines.append("    ./gradlew --no-daemon bootJar -x test --no-build-cache")
    else:
        lines.append("RUN ./gradlew --no-daemon bootJar -x test --no-build-cache")
    lines.append("")

    # Extract stage
    lines.append(f"FROM {build_jdk} AS app-extract")
    lines.append("WORKDIR /app_extracted")
    lines.append("COPY --from=build /app/build/libs/*-SNAPSHOT.jar app.jar")
    lines.append("RUN java -Djarmode=layertools -jar app.jar extract")
    lines.append("")

    if cfg.use_jlink:
        lines.append(f"FROM {jlink_jdk} AS jre-builder")
        lines.append("WORKDIR /app_extracted")
        lines.append("COPY --from=build /app/build/libs/*-SNAPSHOT.jar app.jar")
        lines.append("RUN java -Djarmode=layertools -jar app.jar extract")
        lines.append("RUN jdeps --ignore-missing-deps --recursive --multi-release 25 --print-module-deps \\")
        lines.append("    --class-path 'dependencies/BOOT-INF/lib/*' app.jar > modules.txt")
        lines.append("RUN MODULES=$(tr ',' '\\n' < modules.txt | sort -u | paste -sd, -) && \\")
        lines.append("    jlink --add-modules \"$MODULES\" --strip-debug --no-man-pages --no-header-files --compress=2 --output /opt/custom-java")
        lines.append("")

    if cfg.use_aot_cache:
        lines.append(f"FROM {runtime} AS aot-trainer")
        if cfg.use_jlink:
            lines.append("COPY --from=jre-builder /opt/custom-java /opt/java")
            lines.append("ENV JAVA_HOME=/opt/java")
            lines.append("ENV PATH=\"${JAVA_HOME}/bin:${PATH}\"")
        lines.append("WORKDIR /app")
        lines.append("COPY --from=app-extract /app_extracted/dependencies/ ./")
        lines.append("COPY --from=app-extract /app_extracted/snapshot-dependencies/ ./")
        lines.append("COPY --from=app-extract /app_extracted/spring-boot-loader/ ./")
        lines.append("COPY --from=app-extract /app_extracted/application/ ./")
        lines.append("RUN java -XX:AOTCacheOutput=app.aot -Dspring.context.exit=onRefresh org.springframework.boot.loader.launch.JarLauncher")
        lines.append("")

    lines.append(f"FROM {runtime}")
    lines.append(install_block(cfg.runtime_base, cfg.non_root))

    if cfg.non_root:
        shell = "/sbin/nologin" if cfg.runtime_base == "alpine" else "/usr/sbin/nologin"
        lines.append("RUN groupadd --system --gid 1001 javauser && \\")
        lines.append(f"    useradd --system --uid 1001 --gid 1001 --no-create-home --shell {shell} javauser")

    if cfg.use_jlink:
        lines.append("ENV JAVA_HOME=/opt/java")
        lines.append("ENV PATH=\"${JAVA_HOME}/bin:${PATH}\"")

    if cfg.non_root:
        lines.append("RUN install -d -o 1001 -g 1001 -m 755 /app && install -d -o 1001 -g 1001 -m 1777 /tmp")
    else:
        lines.append("RUN install -d -m 755 /app && install -d -m 1777 /tmp")

    lines.append("WORKDIR /app")

    if cfg.use_jlink:
        lines.append("COPY --from=jre-builder /opt/custom-java /opt/java")

    owner = "--chown=1001:1001 " if cfg.non_root else ""
    lines.append(f"COPY --from=app-extract {owner}/app_extracted/dependencies/ ./")
    lines.append(f"COPY --from=app-extract {owner}/app_extracted/snapshot-dependencies/ ./")
    lines.append(f"COPY --from=app-extract {owner}/app_extracted/spring-boot-loader/ ./")
    lines.append(f"COPY --from=app-extract {owner}/app_extracted/application/ ./")

    if cfg.use_aot_cache:
        lines.append(f"COPY --from=aot-trainer {owner}/app/app.aot ./app.aot")

    lines.append("EXPOSE 8080")
    lines.append("EXPOSE 8081")

    if cfg.healthcheck:
        if cfg.runtime_base == "ubi9-minimal":
            lines.append("HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \\")
            lines.append("  CMD curl -fsS http://localhost:8081/actuator/health/readiness || wget -qO- http://localhost:8081/actuator/health/readiness || exit 1")
        else:
            lines.append("HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \\")
            lines.append("  CMD curl -fsS http://localhost:8081/actuator/health/readiness || exit 1")

    if cfg.non_root:
        lines.append("USER 1001")

    entry = ["java"]
    if cfg.use_aot_cache:
        entry.append("-XX:AOTCache=app.aot")
    if cfg.tuned_jvm_flags:
        entry.extend([
            "-XX:+UseZGC",
            "-XX:MaxRAMPercentage=75",
            "-XX:InitialRAMPercentage=50",
            "-XX:+ExitOnOutOfMemoryError",
            "-Djava.io.tmpdir=/tmp",
        ])
    entry.append("org.springframework.boot.loader.launch.JarLauncher")

    lines.append("ENTRYPOINT [" + ", ".join(f'\"{x}\"' for x in entry) + "]")
    lines.append("")
    return "\n".join(lines)


def build_native_dockerfile(cfg: WizardConfig) -> str:
    s = runtime_settings(cfg.runtime_base, cfg.pin_digests)
    runtime = s["runtime"]

    lines: list[str] = []
    lines.append("# syntax=docker/dockerfile:1")
    lines.append("# Generated by tools/dockerfile_wizard.py (native-image mode)")
    lines.append("FROM ghcr.io/graalvm/native-image-community:25 AS build")
    lines.append("WORKDIR /app")
    lines.append("COPY gradlew build.gradle settings.gradle ./")
    lines.append("COPY gradle ./gradle")
    lines.append("COPY src ./src")
    lines.append("RUN chmod +x gradlew")
    lines.append("RUN ./gradlew --no-daemon nativeCompile -x test")
    lines.append("")
    lines.append(f"FROM {runtime}")
    lines.append(install_block(cfg.runtime_base, cfg.non_root))

    if cfg.non_root:
        shell = "/sbin/nologin" if cfg.runtime_base == "alpine" else "/usr/sbin/nologin"
        lines.append("RUN groupadd --system --gid 1001 javauser && \\")
        lines.append(f"    useradd --system --uid 1001 --gid 1001 --no-create-home --shell {shell} javauser")

    if cfg.non_root:
        lines.append("RUN install -d -o 1001 -g 1001 -m 755 /app && install -d -o 1001 -g 1001 -m 1777 /tmp")
    else:
        lines.append("RUN install -d -m 755 /app && install -d -m 1777 /tmp")

    lines.append("WORKDIR /app")
    owner = "--chown=1001:1001 " if cfg.non_root else ""
    lines.append(f"COPY --from=build {owner}/app/build/native/nativeCompile/app /app/app")
    lines.append("EXPOSE 8080")
    lines.append("EXPOSE 8081")

    if cfg.healthcheck:
        if cfg.runtime_base == "ubi9-minimal":
            lines.append("HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \\")
            lines.append("  CMD curl -fsS http://localhost:8081/actuator/health/readiness || wget -qO- http://localhost:8081/actuator/health/readiness || exit 1")
        else:
            lines.append("HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \\")
            lines.append("  CMD curl -fsS http://localhost:8081/actuator/health/readiness || exit 1")

    if cfg.non_root:
        lines.append("USER 1001")
    lines.append("ENTRYPOINT [\"/app/app\"]")
    lines.append("")
    return "\n".join(lines)


def from_args() -> WizardConfig:
    parser = argparse.ArgumentParser(description="Generate Dockerfile from requirements")
    parser.add_argument("--output", default="Dockerfile.generated", help="Output Dockerfile path")
    parser.add_argument("--profile", choices=sorted(PROFILES.keys()), help="One-flag preset profile")
    parser.add_argument("--runtime-base", choices=["debian-bookworm-slim", "ubuntu-noble", "alpine", "ubi9-minimal", "eclipse-temurin-jre"])
    parser.add_argument("--buildkit-cache", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--jlink", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--aot-cache", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--non-root", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--healthcheck", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--tuned-jvm", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--pin-digests", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--native-image", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--interactive", action="store_true", help="Run interactive wizard")
    args = parser.parse_args()

    if args.interactive or (not args.runtime_base and not args.profile):
        runtime_base = ask_choice(
            "Choose runtime base image strategy:",
            [
                "debian-bookworm-slim",
                "ubuntu-noble",
                "alpine",
                "ubi9-minimal",
                "eclipse-temurin-jre",
            ],
            default_index=1,
        )
        use_buildkit_cache = ask_bool("Use BuildKit Gradle cache mount?", True)
        use_jlink = ask_bool("Use jlink custom runtime?", runtime_base != "eclipse-temurin-jre")
        use_aot_cache = ask_bool("Enable JEP 483 AOT cache training/runtime?", False)
        non_root = ask_bool("Run container as non-root user?", True)
        healthcheck = ask_bool("Add Docker HEALTHCHECK against readiness endpoint?", True)
        tuned_jvm_flags = ask_bool("Use tuned JVM container flags?", True)
        pin_digests = ask_bool("Pin known image digests where available?", False)
        use_native_image = ask_bool("Generate native image Dockerfile instead of JVM?", False)
    else:
        defaults = dict(PROFILES.get(args.profile or "balanced", PROFILES["balanced"]))
        if args.runtime_base:
            defaults["runtime_base"] = args.runtime_base

        runtime_base = str(defaults["runtime_base"])
        use_buildkit_cache = defaults["use_buildkit_cache"] if args.buildkit_cache is None else args.buildkit_cache
        use_jlink = defaults["use_jlink"] if args.jlink is None else args.jlink
        use_aot_cache = defaults["use_aot_cache"] if args.aot_cache is None else args.aot_cache
        non_root = defaults["non_root"] if args.non_root is None else args.non_root
        healthcheck = defaults["healthcheck"] if args.healthcheck is None else args.healthcheck
        tuned_jvm_flags = defaults["tuned_jvm_flags"] if args.tuned_jvm is None else args.tuned_jvm
        pin_digests = defaults["pin_digests"] if args.pin_digests is None else args.pin_digests
        use_native_image = defaults.get("use_native_image", False) if args.native_image is None else args.native_image

    return WizardConfig(
        runtime_base=runtime_base,
        use_buildkit_cache=use_buildkit_cache,
        use_jlink=use_jlink,
        use_aot_cache=use_aot_cache,
        non_root=non_root,
        healthcheck=healthcheck,
        tuned_jvm_flags=tuned_jvm_flags,
        pin_digests=pin_digests,
        use_native_image=use_native_image,
        output=Path(args.output),
    )


def main() -> None:
    cfg = from_args()
    text = build_dockerfile(cfg)
    cfg.output.write_text(text)
    print(f"Generated: {cfg.output}")
    print("Tip: compare with current Dockerfile before replacing it.")


if __name__ == "__main__":
    main()

