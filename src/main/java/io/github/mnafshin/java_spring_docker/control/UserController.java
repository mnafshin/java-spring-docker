package io.github.mnafshin.java_spring_docker.control;

import io.github.mnafshin.java_spring_docker.service.ProductService;
import io.github.mnafshin.java_spring_docker.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.math.BigDecimal;
import java.util.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;
    private final ProductService productService;

    @Autowired
    public UserController(UserService userService, ProductService productService) {
        this.userService = userService;
        this.productService = productService;
    }

    @GetMapping
    public ResponseEntity<Map<String, Object>> getAllUsers() {
        return ResponseEntity.ok(Map.of(
                "users", userService.getAllUsers(),
                "count", userService.getAllUsers().size()
        ));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Object> getUserById(@PathVariable Long id) {
        return userService.getUserById(id)
                .map(user -> ResponseEntity.ok((Object) Map.of(
                        "user", user,
                        "success", true
                )))
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<Object> createUser(
            @RequestParam String name,
            @RequestParam String email) {
        UserService.User user = userService.createUser(name, email);
        return ResponseEntity.ok(Map.of(
                "user", user,
                "success", true
        ));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Object> updateUser(
            @PathVariable Long id,
            @RequestParam String name,
            @RequestParam String email) {
        return userService.updateUser(id, name, email)
                .map(user -> ResponseEntity.ok((Object) Map.of(
                        "user", user,
                        "success", true
                )))
                .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Object> deleteUser(@PathVariable Long id) {
        boolean deleted = userService.deleteUser(id);
        return ResponseEntity.ok(Map.of(
                "deleted", deleted,
                "success", deleted
        ));
    }
}

