package io.github.mnafshin.java_spring_docker.control;

import io.github.mnafshin.java_spring_docker.service.ProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.math.BigDecimal;
import java.util.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    private final ProductService productService;

    @Autowired
    public ProductController(ProductService productService) {
        this.productService = productService;
    }

    @GetMapping
    public ResponseEntity<Map<String, Object>> getAllProducts() {
        return ResponseEntity.ok(Map.of(
                "products", productService.getAllProducts(),
                "count", productService.getAllProducts().size()
        ));
    }

    @GetMapping("/active")
    public ResponseEntity<Map<String, Object>> getActiveProducts() {
        List<ProductService.Product> active = productService.getActiveProducts();
        return ResponseEntity.ok(Map.of(
                "products", active,
                "count", active.size()
        ));
    }

    @GetMapping("/category/{category}")
    public ResponseEntity<Map<String, Object>> getByCategory(@PathVariable String category) {
        List<ProductService.Product> products = productService.getProductsByCategory(category);
        return ResponseEntity.ok(Map.of(
                "products", products,
                "category", category,
                "count", products.size()
        ));
    }

    @GetMapping("/search")
    public ResponseEntity<Map<String, Object>> search(@RequestParam String q) {
        List<ProductService.Product> results = productService.searchProducts(q);
        return ResponseEntity.ok(Map.of(
                "products", results,
                "query", q,
                "count", results.size()
        ));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Object> getProductById(@PathVariable Long id) {
        return productService.getProductById(id)
                .map(product -> ResponseEntity.ok((Object) Map.of(
                        "product", product,
                        "success", true
                )))
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<Object> createProduct(
            @RequestParam String name,
            @RequestParam String category,
            @RequestParam BigDecimal price,
            @RequestParam(defaultValue = "true") boolean active) {
        ProductService.Product product = productService.createProduct(name, category, price, active);
        return ResponseEntity.ok(Map.of(
                "product", product,
                "success", true
        ));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Object> updateProduct(
            @PathVariable Long id,
            @RequestParam String name,
            @RequestParam String category,
            @RequestParam BigDecimal price,
            @RequestParam(defaultValue = "true") boolean active) {
        return productService.updateProduct(id, name, category, price, active)
                .map(product -> ResponseEntity.ok((Object) Map.of(
                        "product", product,
                        "success", true
                )))
                .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Object> deleteProduct(@PathVariable Long id) {
        boolean deleted = productService.deleteProduct(id);
        return ResponseEntity.ok(Map.of(
                "deleted", deleted,
                "success", deleted
        ));
    }
}

