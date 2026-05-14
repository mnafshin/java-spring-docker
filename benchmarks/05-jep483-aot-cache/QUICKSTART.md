# AOT Cache Complex Benchmark - Quick Reference

> Canonical scenario: use `benchmarks/05-jep483-aot-cache/` for active runs and reporting.

## What is This?

An **enterprise-grade Spring Boot application** designed to demonstrate the **real-world benefits of JEP 483 AOT Cache** through realistic complexity.

This demonstrates AOT cache benefits with:
- **Multiple REST controllers** handling CRUD operations
- **Complex service layer** with business logic
- **Spring configurations** with interceptors and exception handlers  
- **Dependency injection complexity** across multiple layers
- **Reflection-heavy initialization** at startup

## Quick Start

### Option 1: Run Complete Benchmark (Recommended)
```bash
cd /path/to/your-java25-project

# Run canonical complex AOT benchmark with 15 samples
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 15
python3 benchmarks/common/analyze_results.py benchmarks/05-jep483-aot-cache/results/raw.csv
```

### Option 2: Run Using Common Script
```bash
# Run with standard analysis
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 15

# Analyze results
python3 benchmarks/common/analyze_results.py benchmarks/05-jep483-aot-cache/results/raw.csv
```

### Option 3: Manual Testing (Educational)
```bash
# Build the application
./gradlew build -x test

# Test each variant manually
docker build -f benchmarks/05-jep483-aot-cache/variants/with-aot-cache/Dockerfile \
  -t demo-aot-with .

docker build -f benchmarks/05-jep483-aot-cache/variants/without-aot-cache/Dockerfile \
  -t demo-aot-without .

# Measure startup with 'time' command
docker run --rm demo-aot-with /bin/true
docker run --rm demo-aot-without /bin/true
```

## Expected Results

```
┌─────────────────────────────────────────────────────┐
│ Typical Startup Times (Complex App)                 │
├─────────────────────────────────────────────────────┤
│ Without AOT Cache:  900ms  ████████████░░░░░░░░░░  │
│ With AOT Cache:     550ms  ███████░░░░░░░░░░░░░░░  │
│ Improvement:        350ms (38% faster) 🚀           │
└─────────────────────────────────────────────────────┘

This can be significantly better than a minimal-app baseline.
```

## Application Structure

### Controllers (REST API)
```
/api/users          - User CRUD operations
/api/products       - Product CRUD operations
/api/info           - Application info (reflection demo)
/api/status         - Health status
/bench/read         - Benchmark read operation
/bench/cpu          - CPU-intensive benchmark
```

### Services
- **UserService** - In-memory user management with stream operations
- **ProductService** - Product catalog with search and filtering

### Configuration
- **WebConfiguration** - CORS, web MVC configuration
- **InterceptorConfiguration** - Request interceptors
- **GlobalExceptionHandler** - Centralized error handling
- **ApplicationStartupListener** - Reflection cache initialization

## Why This Matters

### For Development Teams
Understanding when AOT cache helps informs architectural decisions:
- Microservices with frequent restarts → High ROI
- Long-lived processes → Lower ROI
- Container orchestration environments → Strategic advantage

### For DevOps
Optimize deployment and scaling:
- Faster pod startups in Kubernetes
- Reduced cold-start latency
- Better resource utilization

### For SREs
Better service reliability:
- Faster recovery from failures
- Smoother rolling deployments
- Improved customer experience during incidents

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | This file - benchmarks overview |
| `run_benchmark.sh` | Quick-start script |
| `load_generator.sh` | Load testing for cache warming |
| `analyze_aot_cache.py` | Advanced analysis script |
| `variants/with-aot-cache/Dockerfile` | AOT cache variant |
| `variants/without-aot-cache/Dockerfile` | Baseline variant |
| `variants/minimal-app/Dockerfile` | Control variant |

## Documentation

### Educational Materials
- **[AOT Cache Deep Dive Guide](./AOT-CACHE-GUIDE.md)**
  - What is AOT cache?
  - How does it work?
  - When to use it?
  - Troubleshooting guide

- **[Benchmark Comparison (05 vs 11)](./AOT-CACHE-COMPARISON.md)**
  - Side-by-side comparison
  - Why different results?
  - When to use each?
  - Real-world recommendations

### Benchmark Infrastructure
- **[Common Scripts](../common/README.md)** - Shared utilities
- **[Setup Guide](../setup_benchmark_folders.py)** - Environment setup

## Understanding the Results

### Measurement Accuracy Tips
1. Run **at least 15 samples** per variant for statistical confidence
2. **Disable CPU frequency scaling** if possible:
   ```bash
   sudo turbostat --quiet --show Core,Avg_MHz --interval 1000
   ```
3. Ensure **stable environment** during runs
4. **Close other applications** for consistency
5. Use **same container resource limits** across tests

### Interpreting Statistics
- **Mean**: Average startup time (most important)
- **Median**: Middle value, robust to outliers
- **Std Dev**: Lower is better, shows consistency
- **Min/Max**: Range of observed values

### Statistical Significance
```
Improvement is significant if:
- Improvement > 2× standard deviation
- Improvement > 5% of baseline
- Consistent across all samples
```

## Common Issues & Solutions

### Issue: AOT Cache Not Being Used
```
Symptom: Startup time unchanged with -XX:AOTCache
Solutions:
1. Verify app.aot file exists and is readable
2. Check JVM version (Java 24+)
3. Review logs: java -XX:AOTCache=app.aot -verbose:class
```

### Issue: Cache File Gets Large
```
Symptom: AOT cache file >50MB (unexpected)
Solutions:
1. This is normal for complex apps
2. Compress with Docker multi-stage builds
3. Only include final stage in image
```

### Issue: Inconsistent Results
```
Symptom: High variance in startup times
Solutions:
1. Disable frequency scaling
2. Increase sample count to 20+
3. Ensure stable system load
4. Use --rm flag with docker run
```

## Advanced Topics

### Extending the Benchmark

Add more complexity to demonstrate even greater AOT cache benefits:

1. **Database Integration**
   ```xml
   <dependency>
       <groupId>org.springframework.boot</groupId>
       <artifactId>spring-boot-starter-data-jpa</artifactId>
   </dependency>
   ```
   Entity scanning → more reflection → higher AOT benefit

2. **Security Framework**
   ```xml
   <dependency>
       <groupId>org.springframework.boot</groupId>
       <artifactId>spring-boot-starter-security</artifactId>
   </dependency>
   ```
   Authentication/authorization processing → significant startup work

3. **Caching Layer**
   ```xml
   <dependency>
       <groupId>org.springframework.boot</groupId>
       <artifactId>spring-boot-starter-cache</artifactId>
   </dependency>
   ```
   Cache annotations → reflection-based configuration

### Performance Profiling

Profile startup to understand where AOT helps:
```bash
# Measure class loading time
java -XX:+PrintCompilation \
     -XX:AOTCache=app.aot \
     -cp spring-app.jar \
     org.springframework.boot.loader.JarLauncher

# Profile with JFR
java -XX:StartFlightRecording=filename=recording.jfr \
     -XX:AOTCache=app.aot \
     -cp spring-app.jar \
     org.springframework.boot.loader.JarLauncher
```

## References

- **JEP 483**: https://openjdk.org/jeps/483
- **Spring Boot Documentation**: https://spring.io/projects/spring-boot
- **Docker Best Practices**: https://docs.docker.com/develop/develop-images/
- **Kubernetes Performance**: https://kubernetes.io/docs/concepts/scheduling-eviction/

## Next Steps

1. **Run the benchmark** to see AOT cache benefits
2. **Study the application code** to understand complexity
3. **Review the deep-dive guide** for technical details
4. **Compare with `minimal-app` variant** to see simple vs complex behavior
5. **Adapt to your use case** - add your own patterns and measure

## Questions?

Refer to:
- [AOT Cache Deep Dive Guide](./AOT-CACHE-GUIDE.md)
- [Benchmark Comparison](./AOT-CACHE-COMPARISON.md)
- [Scenario README](./README.md)

---

**Last Updated**: May 13, 2026  
**JDK**: Java 25  
**Spring Boot**: 4.0.1  
**Docker Base**: debian:bookworm-slim

