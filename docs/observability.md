# Runtime observability

`springdocker` does not generate application observability wiring, but the repository now documents a
baseline stack for Spring Boot apps generated from this project.

## Recommended stack

- Micrometer for metrics collection
- Prometheus for scraping and alerting
- OpenTelemetry for traces when an OTLP backend is available
- Grafana for dashboards and trend inspection

## Sample application properties

See `docs/examples/observability/application.properties` for a minimal Spring Boot actuator/metrics setup.

## Sample Prometheus integration

See `docs/examples/observability/service-monitor.yaml` for a simple Prometheus Operator `ServiceMonitor`
example that targets the management endpoint.

## Workflow notes

- `springdocker benchmark analyze` keeps runtime measurement separate from metrics collection.
- The generated Dockerfile and Kubernetes manifests assume a dedicated management port (`8081`) for probes
  and metrics.
- Use structured logging and pod metadata tags so Grafana dashboards can correlate runtime signals with
  benchmark results.

