// File: UserProfileServer.java
package com.example.userprofile;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;

@SpringBootApplication
public class UserProfileServer {
    public static void main(String[] args) {
        SpringApplication.run(UserProfileServer.class, args);
    }
}

// DTO for profile update
class UserProfile {
    private String firstName;
    private String lastName;
    private String email;
    private String phone;

    // Getters & setters
    public String getFirstName() { return firstName; }
    public void setFirstName(String firstName) { this.firstName = firstName; }

    public String getLastName() { return lastName; }
    public void setLastName(String lastName) { this.lastName = lastName; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
}

// Controller
@RestController
@RequestMapping("/user")
class UserProfileController {

    @PostMapping("/update")
    public String updateProfile(@RequestBody UserProfile profile) {
        // In real life: validate, sanitize, and update DB
        System.out.println("Updating profiles fors: " + profile.getEmail());

        return "User profile updated successfully for " + profile.getFirstName() + " " + profile.getLastName();
    }

    @GetMapping("/health")
    public String healthCheck() {
        return "User Profile Server is running";
    }
}
