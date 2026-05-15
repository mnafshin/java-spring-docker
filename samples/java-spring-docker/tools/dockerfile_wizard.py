#!/usr/bin/env python3
"""Interactive Dockerfile wizard for Java 25+ Spring Boot projects.

Generates a production-grade Dockerfile exploiting Java 25+ features:
  - jlink + jdeps custom JRE (requires Java 9+, tuned for 25)
  - JEP 483 AOT class-loading cache (requires Java 24+)

Supports both Gradle and Maven build tools.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WizardConfig:
    runtime_base: str
    use_buildkit_cache: bool
    use_jlink: bool
    use_aot_cache: bool
    non_root: bool
    tuned_jvm_flags: bool
    pin_digests: bool
    use_native_image: bool
    output: Path
    build_tool: str = "gradle"   # "gradle" | "maven"
    java_version: int = 25        # minimum 25 for JEP 483 AOT Cache support
    app_port: int = 8080
    management_port: int = 8081
    source_dir: str = "src"
    jar_glob: str | None = None
    native_bin_path: str | None = None


# ---------------------------------------------------------------------------
# Pinned digests per Java version (extend as new versions are validated)
# ---------------------------------------------------------------------------
_PINNED_JDK: dict[int, str] = {
    25: "eclipse-temurin:25-jdk@sha256:572fe7b5b3ca8beb3b3aca96a7a88f1f7bc98a3bdffd03784a4568962c1a963a",
}
_PINNED_RUNTIME: dict[str, str] = {
    "debian-bookworm-slim": "debian:bookworm-slim@sha256:d5d3f9c23164ea16f31852f95bd5959aad1c5e854332fe00f7b3a20fcc9f635c",
}


PROFILES: dict[str, dict[str, object]] = {
    "balanced": {
        "runtime_base": "debian-bookworm-slim",
        "use_buildkit_cache": True,
        "use_jlink": True,
        "use_aot_cache": False,
        "non_root": True,
        "tuned_jvm_flags": True,
        "pin_digests": False,
        "build_tool": "gradle",
        "java_version": 25,
    },
    "smallest": {
        "runtime_base": "alpine",
        "use_buildkit_cache": True,
        "use_jlink": True,
        "use_aot_cache": False,
        "non_root": True,
        "tuned_jvm_flags": True,
        "pin_digests": False,
        "build_tool": "gradle",
        "java_version": 25,
    },
    "enterprise": {
        "runtime_base": "ubi9-minimal",
        "use_buildkit_cache": True,
        "use_jlink": True,
        "use_aot_cache": False,
        "non_root": True,
        "tuned_jvm_flags": True,
        "pin_digests": False,
        "build_tool": "gradle",
        "java_version": 25,
    },
    "simplest": {
        "runtime_base": "eclipse-temurin-jre",
        "use_buildkit_cache": True,
        "use_jlink": False,
        "use_aot_cache": False,
        "non_root": True,
        "tuned_jvm_flags": True,
        "pin_digests": False,
        "build_tool": "gradle",
        "java_version": 25,
    },
    "coldstart": {
        "runtime_base": "debian-bookworm-slim",
        "use_buildkit_cache": True,
        "use_jlink": True,
        "use_aot_cache": True,
        "non_root": True,
        "tuned_jvm_flags": True,
        "pin_digests": False,
        "use_native_image": False,
        "build_tool": "gradle",
        "java_version": 25,
    },
    "native": {
        "runtime_base": "debian-bookworm-slim",
        "use_buildkit_cache": True,
        "use_jlink": False,
        "use_aot_cache": False,
        "non_root": True,
        "tuned_jvm_flags": False,
        "pin_digests": False,
        "use_native_image": True,
        "build_tool": "gradle",
        "java_version": 25,
    },
}


# ---------------------------------------------------------------------------
# Build-tool helpers
# ---------------------------------------------------------------------------

def _cache_path(build_tool: str) -> str:
    return "/root/.m2" if build_tool == "maven" else "/root/.gradle"


def _build_setup_lines(cfg: WizardConfig) -> list[str]:
    """COPY + pre-exec lines for the chosen build tool."""
    if cfg.build_tool == "maven":
        return [
            "COPY mvnw pom.xml ./",
            "COPY .mvn ./.mvn",
            "RUN chmod +x mvnw",
        ]
    return [
        "COPY gradlew build.gradle settings.gradle ./",
        "COPY gradle ./gradle",
        "RUN chmod +x gradlew",
    ]


def _deps_cmd_lines(cfg: WizardConfig) -> list[str]:
    """Dependency pre-warm command (with or without BuildKit cache mount)."""
    if cfg.build_tool == "maven":
        cmd = "./mvnw -B -q dependency:go-offline"
    else:
        cmd = "./gradlew --no-daemon dependencies -q"
    if cfg.use_buildkit_cache:
        cache = _cache_path(cfg.build_tool)
        return [
            f"RUN --mount=type=cache,sharing=locked,target={cache} \\",
            f"    {cmd}",
        ]
    return [f"RUN {cmd}"]


def _build_jar_lines(cfg: WizardConfig) -> list[str]:
    """JAR / package build command (with or without BuildKit cache mount)."""
    if cfg.build_tool == "maven":
        cmd = "./mvnw -B -q package -DskipTests"
    else:
        cmd = "./gradlew --no-daemon bootJar -x test --no-build-cache"
    if cfg.use_buildkit_cache:
        cache = _cache_path(cfg.build_tool)
        return [
            f"RUN --mount=type=cache,sharing=locked,target={cache} \\",
            f"    {cmd}",
        ]
    return [f"RUN {cmd}"]


def _jar_artifact_path(cfg: WizardConfig) -> str:
    if cfg.jar_glob:
        return cfg.jar_glob
    return "target/*.jar" if cfg.build_tool == "maven" else "build/libs/*-SNAPSHOT.jar"


def _optional_musthave_modules_csv() -> str:
    """Return comma-separated modules from musthave_modules.txt, if present."""
    path = Path("musthave_modules.txt")
    if not path.exists():
        return ""
    modules: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        modules.append(line)
    return ",".join(modules)


def _native_build_lines(cfg: WizardConfig) -> list[str]:
    """Native-image compilation command."""
    if cfg.build_tool == "maven":
        return ["RUN ./mvnw -B -q -Pnative native:compile -DskipTests"]
    return ["RUN ./gradlew --no-daemon nativeCompile -x test"]


# ---------------------------------------------------------------------------
# Existing helpers (unchanged interface)
# ---------------------------------------------------------------------------

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


def runtime_settings(runtime_base: str, pin_digests: bool, java_version: int = 25) -> dict[str, str]:
    build_jdk = f"eclipse-temurin:{java_version}-jdk"
    if pin_digests and java_version in _PINNED_JDK:
        build_jdk = _PINNED_JDK[java_version]

    base_map = {
        "debian-bookworm-slim": "debian:bookworm-slim",
        "ubuntu-noble": "ubuntu:24.04",
        "alpine": f"eclipse-temurin:{java_version}-jdk-alpine",
        "ubi9-minimal": "redhat/ubi9-minimal",
        "eclipse-temurin-jre": f"eclipse-temurin:{java_version}-jre",
    }
    runtime = base_map[runtime_base]
    if pin_digests and runtime_base in _PINNED_RUNTIME:
        runtime = _PINNED_RUNTIME[runtime_base]

    return {
        "build_jdk": build_jdk,
        "jlink_jdk": f"eclipse-temurin:{java_version}-jdk-alpine" if runtime_base == "alpine" else build_jdk,
        "runtime": runtime,
    }


def install_block(runtime_base: str, need_user_tools: bool) -> str:
    if runtime_base == "alpine":
        if not need_user_tools:
            return "RUN true"
        return "RUN apk add --no-cache shadow"
    if runtime_base == "ubi9-minimal":
        pkgs = []
        if need_user_tools:
            pkgs.append("shadow-utils")
        if not pkgs:
            return "RUN true"
        return "RUN microdnf install -y --setopt=tsflags=nodocs " + " ".join(pkgs) + " && microdnf clean all"
    pkgs = []
    if need_user_tools:
        pkgs.append("passwd")
    if not pkgs:
        return "RUN true"
    return "RUN apt-get update && apt-get install -y --no-install-recommends " + " ".join(pkgs) + " && rm -rf /var/lib/apt/lists/*"


def build_dockerfile(cfg: WizardConfig) -> str:
    if cfg.use_native_image:
        return build_native_dockerfile(cfg)

    use_jlink = cfg.use_jlink and cfg.runtime_base != "eclipse-temurin-jre"
    use_aot_cache = cfg.use_aot_cache and use_jlink

    s = runtime_settings(cfg.runtime_base, cfg.pin_digests, cfg.java_version)
    build_jdk = s["build_jdk"]
    jlink_jdk = s["jlink_jdk"]
    runtime = s["runtime"]
    jar_path = _jar_artifact_path(cfg)
    musthave_modules_csv = _optional_musthave_modules_csv().replace('"', '\\"')

    lines: list[str] = []
    lines.append("# syntax=docker/dockerfile:1")
    lines.append("# Generated by tools/dockerfile_wizard.py")
    lines.append(f"# Java {cfg.java_version}  |  build-tool: {cfg.build_tool}")
    lines.append("")

    # ── Stage 1: build ──────────────────────────────────────────────────────
    lines.append(f"FROM {build_jdk} AS build")
    lines.append("WORKDIR /app")
    lines.extend(_build_setup_lines(cfg))
    lines.extend(_deps_cmd_lines(cfg))
    lines.append(f"COPY {cfg.source_dir} ./src")
    lines.extend(_build_jar_lines(cfg))
    lines.append("")

    # ── Stage 2: layer extraction ────────────────────────────────────────────
    lines.append(f"FROM {build_jdk} AS app-extract")
    lines.append("WORKDIR /app_extracted")
    lines.append(f"COPY --from=build /app/{jar_path} app.jar")
    lines.append("RUN java -Djarmode=layertools -jar app.jar extract")
    lines.append("")

    # ── Stage 3 (optional): custom JRE via jlink ─────────────────────────────
    if use_jlink:
        lines.append(f"FROM {jlink_jdk} AS jre-builder")
        lines.append("WORKDIR /app_extracted")
        lines.append(f"COPY --from=build /app/{jar_path} app.jar")
        lines.append("RUN java -Djarmode=layertools -jar app.jar extract")
        lines.append(
            f"RUN jdeps --ignore-missing-deps --recursive "
            f"--multi-release {cfg.java_version} --print-module-deps \\"
        )
        lines.append("    --class-path 'dependencies/BOOT-INF/lib/*' app.jar > modules.txt")
        # Merge optional must-have modules resolved at generation time, then jlink.
        lines.append(f'ARG MUSTHAVE_MODULES="{musthave_modules_csv}"')
        lines.append("RUN set -eux; \\")
        lines.append("    MODULES=$( (tr ',' '\\n' < modules.txt; \\")
        lines.append("        printf '%s\\n' \"$MUSTHAVE_MODULES\" | tr ',' '\\n') \\")
        lines.append("        | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \\")
        lines.append("        | grep -v '^$' | sort -u | paste -sd, -); \\")
        lines.append("    echo \"Resolved modules: $MODULES\"; \\")
        lines.append("    jlink --add-modules \"$MODULES\" \\")
        lines.append("          --strip-debug --no-man-pages --no-header-files \\")
        lines.append("          --compress=2 --output /opt/custom-java")
        lines.append("")

    # ── Stage 4 (optional): JEP 483 AOT cache training run ─────────────────
    if use_aot_cache:
        lines.append(f"FROM {runtime} AS aot-trainer")
        lines.append("COPY --from=jre-builder /opt/custom-java /opt/java")
        lines.append("ENV JAVA_HOME=/opt/java")
        lines.append('ENV PATH="${JAVA_HOME}/bin:${PATH}"')
        lines.append("WORKDIR /app")
        lines.append("COPY --from=app-extract /app_extracted/dependencies/ ./")
        lines.append("COPY --from=app-extract /app_extracted/snapshot-dependencies/ ./")
        lines.append("COPY --from=app-extract /app_extracted/spring-boot-loader/ ./")
        lines.append("COPY --from=app-extract /app_extracted/application/ ./")
        lines.append(
            "RUN java -XX:AOTCacheOutput=app.aot -Dspring.context.exit=onRefresh "
            "org.springframework.boot.loader.launch.JarLauncher; \\"
        )
        lines.append("    test -f app.aot")
        lines.append("")

    # ── Stage 5: runtime ────────────────────────────────────────────────────
    lines.append(f"FROM {runtime}")
    lines.append(install_block(cfg.runtime_base, cfg.non_root))

    if cfg.non_root:
        shell = "/sbin/nologin" if cfg.runtime_base == "alpine" else "/usr/sbin/nologin"
        lines.append("RUN groupadd --system --gid 1001 javauser && \\")
        lines.append(f"    useradd --system --uid 1001 --gid 1001 --no-create-home --shell {shell} javauser")

    if use_jlink:
        lines.append("ENV JAVA_HOME=/opt/java")
        lines.append('ENV PATH="${JAVA_HOME}/bin:${PATH}"')

    if cfg.non_root:
        lines.append("RUN install -d -o 1001 -g 1001 -m 755 /app && install -d -o 1001 -g 1001 -m 1777 /tmp")
    else:
        lines.append("RUN install -d -m 755 /app && install -d -m 1777 /tmp")

    lines.append("WORKDIR /app")

    if use_jlink:
        lines.append("COPY --from=jre-builder /opt/custom-java /opt/java")

    owner = "--chown=1001:1001 " if cfg.non_root else ""
    lines.append(f"COPY --from=app-extract {owner}/app_extracted/dependencies/ ./")
    lines.append(f"COPY --from=app-extract {owner}/app_extracted/snapshot-dependencies/ ./")
    lines.append(f"COPY --from=app-extract {owner}/app_extracted/spring-boot-loader/ ./")
    lines.append(f"COPY --from=app-extract {owner}/app_extracted/application/ ./")

    if use_aot_cache:
        lines.append(f"COPY --from=aot-trainer {owner}/app/app.aot ./app.aot")

    lines.append(f"EXPOSE {cfg.app_port}")
    if cfg.management_port != cfg.app_port:
        lines.append(f"EXPOSE {cfg.management_port}")

    if cfg.non_root:
        lines.append("USER 1001")

    entry = ["java"]
    if use_aot_cache:
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

    lines.append("ENTRYPOINT [" + ", ".join(f'"{x}"' for x in entry) + "]")
    lines.append("")
    return "\n".join(lines)


def build_native_dockerfile(cfg: WizardConfig) -> str:
    s = runtime_settings(cfg.runtime_base, cfg.pin_digests, cfg.java_version)
    runtime = s["runtime"]

    lines: list[str] = []
    lines.append("# syntax=docker/dockerfile:1")
    lines.append("# Generated by tools/dockerfile_wizard.py (native-image mode)")
    lines.append(f"# Java {cfg.java_version}  |  build-tool: {cfg.build_tool}")
    lines.append(f"FROM ghcr.io/graalvm/native-image-community:{cfg.java_version} AS build")
    lines.append("WORKDIR /app")
    lines.extend(_build_setup_lines(cfg))
    lines.append(f"COPY {cfg.source_dir} ./src")
    lines.extend(_native_build_lines(cfg))
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
    # Allow callers to override native binary path for custom artifact names.
    if cfg.native_bin_path:
        native_bin = cfg.native_bin_path
    elif cfg.build_tool == "maven":
        native_bin = "/app/target/app"
    else:
        native_bin = "/app/build/native/nativeCompile/app"
    lines.append(f"COPY --from=build {owner}{native_bin} /app/app")
    lines.append(f"EXPOSE {cfg.app_port}")
    if cfg.management_port != cfg.app_port:
        lines.append(f"EXPOSE {cfg.management_port}")

    if cfg.non_root:
        lines.append("USER 1001")
    lines.append('ENTRYPOINT ["/app/app"]')
    lines.append("")
    return "\n".join(lines)


def from_args() -> WizardConfig:
    parser = argparse.ArgumentParser(
        description="Generate a Java 25+ Dockerfile from requirements (jlink + JEP 483 AOT aware)"
    )
    parser.add_argument("--output", default="Dockerfile.generated", help="Output Dockerfile path")
    parser.add_argument("--profile", choices=sorted(PROFILES.keys()), help="One-flag preset profile")
    parser.add_argument("--build-tool", choices=["gradle", "maven"], default=None,
                        help="Build tool used by the project (default: gradle)")
    parser.add_argument("--java-version", type=int, default=None,
                        help="Java major version (default: 25; minimum 25 for JEP 483 AOT Cache)")
    parser.add_argument("--runtime-base", choices=["debian-bookworm-slim", "ubuntu-noble", "alpine", "ubi9-minimal", "eclipse-temurin-jre"])
    parser.add_argument("--buildkit-cache", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--jlink", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--aot-cache", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--non-root", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--tuned-jvm", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--pin-digests", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--native-image", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--app-port", type=int, default=8080,
                        help="Application port exposed by the container (default: 8080)")
    parser.add_argument("--management-port", type=int, default=8081,
                        help="Management/readiness port exposed by the container (default: 8081)")
    parser.add_argument("--source-dir", default="src",
                        help="Relative source directory copied into the build stage (default: src)")
    parser.add_argument("--jar-glob", default=None,
                        help="Override built JAR glob path (example: build/libs/*.jar or target/*.jar)")
    parser.add_argument("--native-bin-path", default=None,
                        help="Override native binary path in build stage (absolute path inside container)")
    parser.add_argument("--interactive", action="store_true", help="Run interactive wizard")
    args = parser.parse_args()

    if args.interactive or (not args.runtime_base and not args.profile):
        build_tool = ask_choice(
            "Choose build tool:",
            ["gradle", "maven"],
            default_index=1,
        )
        java_version_str = input("\nJava major version [25]: ").strip()
        java_version = int(java_version_str) if java_version_str.isdigit() else 25
        if java_version < 25:
            print(f"Warning: JEP 483 AOT Cache requires Java 24+. Using {java_version} — AOT cache will be unavailable.")
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
        use_buildkit_cache = ask_bool(f"Use BuildKit {build_tool} cache mount?", True)
        use_jlink = ask_bool("Use jlink custom runtime? (Java 25+ recommended)", runtime_base != "eclipse-temurin-jre")
        use_aot_cache = ask_bool("Enable JEP 483 AOT cache training/runtime? (Java 25+)", False)
        non_root = ask_bool("Run container as non-root user?", True)
        tuned_jvm_flags = ask_bool("Use tuned JVM container flags?", True)
        pin_digests = ask_bool("Pin known image digests where available?", False)
        use_native_image = ask_bool("Generate native image Dockerfile instead of JVM?", False)
    else:
        defaults = dict(PROFILES.get(args.profile or "balanced", PROFILES["balanced"]))
        if args.runtime_base:
            defaults["runtime_base"] = args.runtime_base

        build_tool = str(args.build_tool or defaults.get("build_tool", "gradle"))
        java_version = int(args.java_version or defaults.get("java_version", 25))
        runtime_base = str(defaults["runtime_base"])
        use_buildkit_cache = defaults["use_buildkit_cache"] if args.buildkit_cache is None else args.buildkit_cache
        use_jlink = defaults["use_jlink"] if args.jlink is None else args.jlink
        use_aot_cache = defaults["use_aot_cache"] if args.aot_cache is None else args.aot_cache
        non_root = defaults["non_root"] if args.non_root is None else args.non_root
        tuned_jvm_flags = defaults["tuned_jvm_flags"] if args.tuned_jvm is None else args.tuned_jvm
        pin_digests = defaults["pin_digests"] if args.pin_digests is None else args.pin_digests
        use_native_image = defaults.get("use_native_image", False) if args.native_image is None else args.native_image

    return WizardConfig(
        runtime_base=runtime_base,
        use_buildkit_cache=use_buildkit_cache,
        use_jlink=use_jlink,
        use_aot_cache=use_aot_cache,
        non_root=non_root,
        tuned_jvm_flags=tuned_jvm_flags,
        pin_digests=pin_digests,
        use_native_image=use_native_image,
        output=Path(args.output),
        build_tool=build_tool,
        java_version=java_version,
        app_port=args.app_port,
        management_port=args.management_port,
        source_dir=args.source_dir,
        jar_glob=args.jar_glob,
        native_bin_path=args.native_bin_path,
    )


def main() -> None:
    cfg = from_args()
    if cfg.java_version < 25:
        print(f"Warning: Java {cfg.java_version} < 25. JEP 483 AOT Cache requires Java 24+.")
    text = build_dockerfile(cfg)
    cfg.output.write_text(text, encoding='utf-8')
    print(f"Generated: {cfg.output}")
    print("Tip: compare with current Dockerfile before replacing it.")


if __name__ == "__main__":
    main()
