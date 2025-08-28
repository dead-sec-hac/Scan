// MyAuthController.java
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> loginRequest) {
        // Login logic
        return ResponseEntity.ok(Map.of("message", "Logins Successful"));
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody Map<String, String> registerRequest) {
        // Registration logic
        return ResponseEntity.ok(Map.of("message", "Registration successful"));
    }

    @GetMapping("/profile/{userId}")
    public ResponseEntity<String> getUserProfile(@PathVariable String userId) {
        return ResponseEntity.ok("Profile for " + userId);
    }
}

@RestController
@RequestMapping("/api/product")
class ProductController {
    @GetMapping("/")
    public ResponseEntity<String> getAllProducts() {
        return ResponseEntity.ok("List of products");
    }

    @PostMapping("/add")
    public ResponseEntity<String> addProduct(@RequestBody Map<String, Object> productData) {
        return ResponseEntity.ok("Product added: " + productData.get("name"));
    }
}
