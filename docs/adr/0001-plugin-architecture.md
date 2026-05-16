# ADR 0001: Plugin architecture

## Status

Accepted

## Context

The CLI needs a small extension point for post-processing generated Dockerfiles without turning the core
generator into a plugin framework for every command.

## Decision

Use a Dockerfile mutator entry-point group (`springdocker.dockerfile_mutators`) with isolated failure
handling. Mutators may be objects or callables that accept the rendered Dockerfile text and the structured
`DockerfileOptions`.

## Consequences

- Downstream projects can customize generated Dockerfiles without forking the CLI.
- Plugin failures do not block generation of the base Dockerfile.
- The extension model stays narrow and focused on Dockerfile generation.

