package io.github.mnafshin.java_spring_docker.config;

import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import java.time.Instant;

@Component
public class ApplicationStartupListener {

    private static final long START_TIME = System.currentTimeMillis();

    @EventListener(ApplicationReadyEvent.class)
    public void onApplicationReady() {
        long elapsed = System.currentTimeMillis() - START_TIME;
        System.out.println("Application ready in " + elapsed + "ms");

        // Trigger some reflection-based work to populate reflection caches
        initializeReflectionCaches();
    }

    private void initializeReflectionCaches() {
        try {
            // Force loading of common reflection-related classes
            Class<?> arrayClasses[] = {
                String.class, Integer.class, Long.class, Double.class, Boolean.class,
                java.util.Map.class, java.util.List.class, java.util.Set.class,
                java.util.HashMap.class, java.util.ArrayList.class, java.util.HashSet.class,
                java.time.LocalDateTime.class, java.time.Instant.class, java.util.Date.class
            };

            for (Class<?> clazz : arrayClasses) {
                // Access class metadata to trigger reflection
                clazz.getDeclaredMethods();
                clazz.getDeclaredFields();
                clazz.getDeclaredConstructors();
            }
        } catch (Exception e) {
            // Ignore exceptions during reflection cache population
        }
    }
}

