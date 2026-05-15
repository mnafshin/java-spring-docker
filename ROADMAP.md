# Roadmap

## Near term

- Improve project documentation and onboarding.
- Expand benchmark reporting and methodology docs.
- Keep the CLI command reference aligned with the implementation.

## Mid term

- Add inspection and explanation workflows for generated Dockerfiles.
- Add container hardening and runtime strategy variants.
- Improve benchmark regression detection.

## Longer term

- Add multi-architecture image support.
- Add release engineering and distribution channels.
- Add richer compatibility and comparison reporting.
- Add a GraalVM/native-image workflow that plugs into the existing benchmark scenarios.

## Native image strategy

- Feasibility: treat native-image as an optional optimization path, not the default packaging path.
- Constraints: GraalVM availability, longer build times, reflection/resource configuration, and platform-specific binaries.
- Workflow: detect a native profile, generate a native build variant, and compare it against the JVM baseline.
- Benchmark integration: use the existing native-vs-jvm benchmark scenario as the comparison entry point.

## Notes

Roadmap items are intentionally ordered from lowest risk to highest integration cost.
