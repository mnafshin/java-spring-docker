package io.github.mnafshin.java_spring_docker.service;

import org.springframework.stereotype.Service;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class UserService {
    private final Map<Long, User> users = new ConcurrentHashMap<>();
    private long idCounter = 1;

    public UserService() {
        // Initialize with sample data
        for (int i = 0; i < 10; i++) {
            User user = new User(idCounter++, "User" + i, "user" + i + "@example.com");
            users.put(user.getId(), user);
        }
    }

    public User createUser(String name, String email) {
        User user = new User(idCounter++, name, email);
        users.put(user.getId(), user);
        return user;
    }

    public Optional<User> getUserById(Long id) {
        return Optional.ofNullable(users.get(id));
    }

    public List<User> getAllUsers() {
        return new ArrayList<>(users.values());
    }

    public Optional<User> updateUser(Long id, String name, String email) {
        return Optional.ofNullable(users.computeIfPresent(id, (k, v) -> {
            v.setName(name);
            v.setEmail(email);
            return v;
        }));
    }

    public boolean deleteUser(Long id) {
        return users.remove(id) != null;
    }

    public static class User {
        private Long id;
        private String name;
        private String email;
        private String createdAt;

        public User(Long id, String name, String email) {
            this.id = id;
            this.name = name;
            this.email = email;
            this.createdAt = new java.util.Date().toString();
        }

        public Long getId() { return id; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getEmail() { return email; }
        public void setEmail(String email) { this.email = email; }
        public String getCreatedAt() { return createdAt; }
    }
}

