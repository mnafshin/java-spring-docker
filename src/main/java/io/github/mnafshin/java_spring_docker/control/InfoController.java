package io.github.mnafshin.java_spring_docker.control;

import io.github.mnafshin.java_spring_docker.config.WebConfiguration;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.lang.management.ManagementFactory;
import java.lang.management.RuntimeMXBean;
import java.lang.management.MemoryMXBean;
import java.util.*;

@RestController
@RequestMapping("/api")
public class InfoController {

    private final WebConfiguration.AppProperties appProperties;

    @Autowired
    public InfoController(WebConfiguration.AppProperties appProperties) {
        this.appProperties = appProperties;
    }

    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> getAppInfo() {
        RuntimeMXBean runtimeMX = ManagementFactory.getRuntimeMXBean();
        MemoryMXBean memoryMX = ManagementFactory.getMemoryMXBean();

        return ResponseEntity.ok(Map.of(
                "app", Map.of(
                        "name", appProperties.getAppName(),
                        "version", appProperties.getVersion(),
                        "environment", appProperties.getEnvironment()
                ),
                "runtime", Map.of(
                        "uptime", runtimeMX.getUptime(),
                        "startTime", runtimeMX.getStartTime(),
                        "javaVersion", System.getProperty("java.version"),
                        "vmName", runtimeMX.getVmName(),
                        "vmVendor", runtimeMX.getVmVendor(),
                        "osName", System.getProperty("os.name"),
                        "osVersion", System.getProperty("os.version"),
                        "osArch", System.getProperty("os.arch"),
                        "availableProcessors", Runtime.getRuntime().availableProcessors()
                ),
                "memory", Map.of(
                        "heapUsed", memoryMX.getHeapMemoryUsage().getUsed(),
                        "heapMax", memoryMX.getHeapMemoryUsage().getMax(),
                        "nonHeapUsed", memoryMX.getNonHeapMemoryUsage().getUsed()
                ),
                "timestamp", System.currentTimeMillis()
        ));
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getStatus() {
        return ResponseEntity.ok(Map.of(
                "status", "UP",
                "timestamp", new Date(),
                "application", appProperties.getAppName(),
                "checks", Map.of(
                        "database", "UP",
                        "cache", "UP",
                        "messaging", "UP"
                )
        ));
    }

    @GetMapping("/system-info")
    public ResponseEntity<Map<String, Object>> getSystemInfo() {
        @SuppressWarnings("unchecked")
        Map<String, Object> environment = (Map<String, Object>) (Map<?, ?>) System.getProperties();

        return ResponseEntity.ok(Map.of(
                "properties", environment,
                "timestamp", System.currentTimeMillis()
        ));
    }
}



