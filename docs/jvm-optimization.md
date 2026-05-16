# JVM optimization strategies

`springdocker` currently supports a small, explicit set of JVM/runtime choices in generated Dockerfiles.

## Current defaults

- non-root runtime user
- `-XX:MaxRAMPercentage=75`
- `-XX:+ExitOnOutOfMemoryError`
- `-Djava.io.tmpdir=/tmp`
- optional jlink runtime stage

## Why these choices exist

- `MaxRAMPercentage` keeps container memory use proportional to the cgroup limit.
- `ExitOnOutOfMemoryError` fails fast instead of leaving a stuck JVM.
- `java.io.tmpdir=/tmp` keeps temporary writes inside the container filesystem.
- jlink reduces the runtime surface area when a custom runtime is appropriate.

## Tradeoffs

| Strategy | Benefit | Cost |
|---|---|---|
| Plain JRE | simplest runtime | larger image |
| jlink runtime | smaller and more controlled runtime | extra build step |
| tuned JVM flags | better container defaults | less JVM portability across workloads |

## Current scope

The CLI does not yet model GC tuning, CDS toggles, or AOT-specific runtime switches as first-class options.
The benchmark analyzer can still surface optional GC/allocation/startup-phase profiling columns when they
are present in `raw.csv`.
