# springdocker positioning

`springdocker` targets the middle ground between black-box image builders and fully hand-written Dockerfiles:

- You get a generated Dockerfile with strong defaults.
- You keep direct ownership of the container definition.
- You can explain and verify the output in CI.

## Why not Jib?

Jib is excellent when you want fast Java image builds without writing Dockerfiles.  
The tradeoff is reduced direct control over the final Dockerfile-level shape.

Choose Jib when:
- your team wants minimal container-layer customization
- Dockerfile ownership is not required

Choose springdocker when:
- your team wants a real Dockerfile artifact in-repo
- you need explicit, reviewable container decisions

## Why not Buildpacks / Paketo / `spring-boot:build-image`?

Buildpacks are great for zero-configuration builds and ecosystem integration.  
The tradeoff is an opinionated build pipeline that can feel opaque when debugging image-level behavior.

Choose Buildpacks when:
- platform defaults are enough
- your team is comfortable with buildpack internals and lifecycle behavior

Choose springdocker when:
- you need explicit Dockerfile ownership
- you want explainable, reviewable Dockerfile output as a first-class artifact

## Why not hand-written Dockerfiles?

Hand-written Dockerfiles maximize control and flexibility, but they are easy to drift and costly to keep aligned with evolving best practices.

Choose hand-written Dockerfiles when:
- your image has highly custom constraints that generators cannot model

Choose springdocker when:
- you want a maintainable baseline generated from repeatable conventions
- you still want manual control after generation

## Summary

springdocker is for teams that want:

1. a Dockerfile they can own and edit
2. opinionated defaults for Spring Boot containerization
3. explain-and-verify workflows around the generated output
