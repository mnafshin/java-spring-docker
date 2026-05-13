package io.github.mnafshin.java_spring_docker.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.CorsRegistry;

@Configuration
public class WebConfiguration implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .maxAge(3600);
    }

    @Bean
    public AppProperties appProperties() {
        return new AppProperties();
    }

    public static class AppProperties {
        private String appName = "Java Spring Docker";
        private String version = "0.0.1-SNAPSHOT";
        private String environment = "production";

        public String getAppName() { return appName; }
        public void setAppName(String appName) { this.appName = appName; }
        public String getVersion() { return version; }
        public void setVersion(String version) { this.version = version; }
        public String getEnvironment() { return environment; }
        public void setEnvironment(String environment) { this.environment = environment; }
    }
}


