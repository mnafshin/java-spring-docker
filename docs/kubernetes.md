# Kubernetes support

`springdocker` does not generate Kubernetes manifests yet, but the repository now carries a baseline
Kubernetes deployment strategy for the sample Spring Boot project.

## What is provided

- `samples/java-spring-docker/k8s/deployment.yaml`
- `samples/java-spring-docker/k8s/service.yaml`
- `samples/java-spring-docker/k8s/kustomization.yaml`

## Default assumptions

- the app exposes HTTP on `8080`
- management endpoints are exposed on `8081`
- readiness probes use `/actuator/health/readiness`
- liveness and startup probes use `/actuator/health/liveness`
- the container runs as UID/GID `1001`
- `/tmp` is writable when `readOnlyRootFilesystem: true`
- default resource requests/limits are included for the sample workload

## Kustomize flow

Apply the sample with:

```bash
kubectl apply -k samples/java-spring-docker/k8s
```

The overlay keeps the sample manifest deterministic while still letting downstream users swap the image,
namespace, or labels without editing the base document.

## When to customize

Adjust the sample manifests if your application:

1. does not use Spring Boot Actuator
2. exposes management endpoints on a different port
3. requires different memory or CPU requests/limits
4. uses a different run-as user or filesystem policy
