package io.github.mnafshin.java_spring_docker.service;

import org.springframework.stereotype.Service;
import java.math.BigDecimal;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

@Service
public class ProductService {
    private final Map<Long, Product> products = new ConcurrentHashMap<>();
    private long idCounter = 1000;

    public ProductService() {
        // Initialize with sample products
        String[] categories = {"Electronics", "Books", "Clothing", "Home & Garden", "Sports"};
        String[] names = {"Laptop", "Novel", "T-Shirt", "Plant Pot", "Running Shoes"};

        for (int i = 0; i < 50; i++) {
            Product product = new Product(
                idCounter++,
                names[i % names.length] + " " + (i / names.length + 1),
                categories[i % categories.length],
                BigDecimal.valueOf(10 + (i * 1.5)),
                Math.random() > 0.2
            );
            products.put(product.getId(), product);
        }
    }

    public Product createProduct(String name, String category, BigDecimal price, boolean active) {
        Product product = new Product(idCounter++, name, category, price, active);
        products.put(product.getId(), product);
        return product;
    }

    public Optional<Product> getProductById(Long id) {
        return Optional.ofNullable(products.get(id));
    }

    public List<Product> getAllProducts() {
        return new ArrayList<>(products.values());
    }

    public List<Product> getActiveProducts() {
        return products.values().stream()
                .filter(Product::isActive)
                .collect(Collectors.toList());
    }

    public List<Product> getProductsByCategory(String category) {
        return products.values().stream()
                .filter(p -> p.getCategory().equalsIgnoreCase(category))
                .collect(Collectors.toList());
    }

    public List<Product> searchProducts(String query) {
        String lowerQuery = query.toLowerCase();
        return products.values().stream()
                .filter(p -> p.getName().toLowerCase().contains(lowerQuery) ||
                           p.getCategory().toLowerCase().contains(lowerQuery))
                .collect(Collectors.toList());
    }

    public Optional<Product> updateProduct(Long id, String name, String category, BigDecimal price, boolean active) {
        return Optional.ofNullable(products.computeIfPresent(id, (k, v) -> {
            v.setName(name);
            v.setCategory(category);
            v.setPrice(price);
            v.setActive(active);
            return v;
        }));
    }

    public boolean deleteProduct(Long id) {
        return products.remove(id) != null;
    }

    public static class Product {
        private Long id;
        private String name;
        private String category;
        private BigDecimal price;
        private boolean active;
        private String createdAt;

        public Product(Long id, String name, String category, BigDecimal price, boolean active) {
            this.id = id;
            this.name = name;
            this.category = category;
            this.price = price;
            this.active = active;
            this.createdAt = new java.util.Date().toString();
        }

        public Long getId() { return id; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }
        public BigDecimal getPrice() { return price; }
        public void setPrice(BigDecimal price) { this.price = price; }
        public boolean isActive() { return active; }
        public void setActive(boolean active) { this.active = active; }
        public String getCreatedAt() { return createdAt; }
    }
}

