package io.github.mnafshin.java_spring_docker.control;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class BenchmarkController {

    @GetMapping("/bench/read")
    public Map<String, Object> read() {
        return Map.of(
                "service", "java-spring-docker",
                "status", "ok",
                "version", "0.0.1-SNAPSHOT"
        );
    }

    @GetMapping("/bench/cpu")
    public Map<String, Object> cpu(@RequestParam(defaultValue = "12000") int work) {
        int boundedWork = Math.max(1000, Math.min(work, 200000));

        long acc = 1125899906842597L;
        for (int i = 0; i < boundedWork; i++) {
            acc ^= (i * 0x9E3779B97F4A7C15L);
            acc = Long.rotateLeft(acc, 13) * 0xC2B2AE3D27D4EB4FL;
        }

        return Map.of(
                "work", boundedWork,
                "checksum", Long.toUnsignedString(acc)
        );
    }
}

