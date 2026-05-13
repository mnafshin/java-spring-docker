# 06 - Runtime hardening (non-root + writable tmp)

## Current implementation

- Create fixed UID/GID 1001 user.
- Run container as non-root.
- Prepare `/tmp` for writable scratch space.

## Why this matters

Running as root by default increases blast radius. A writable temp path is often required by JVM/libs.

## Possible ways

### Option A: root user runtime
- Pros: simplest
- Cons: security anti-pattern

### Option B: non-root with ad-hoc user id
- Pros: better than root
- Cons: UID mismatch issues with Kubernetes policies/volumes

### Option C: non-root fixed UID/GID + explicit tmp handling (current)
- Pros: predictable policy alignment and safer runtime
- Cons: requires file ownership discipline in Dockerfile

## Benchmark strategy

This point is mostly security/operability. Measure reliability impact:

- Run startup + smoke tests under `readOnlyRootFilesystem` style settings
- Verify no permission-related failures
- Track incident count related to fs/user permissions

## Result template

| Variant | Startup success rate | Permission errors | Notes |
|---|---:|---:|---|
| A root | | | |
| B non-root ad-hoc | | | |
| C fixed UID/GID + tmp | | | |

## Benchmark results

**Winner:** `hardened-non-root` — policy decision (security / reliability)

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| hardened-non-root | 5 | 618 | 1204 | 1596 | 103.02 | 100.0% |
| root-runtime | 5 | 1001 | 1199 | 1593 | 103.02 | 100.0% |
