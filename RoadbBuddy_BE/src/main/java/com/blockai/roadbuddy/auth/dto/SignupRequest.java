package com.blockai.roadbuddy.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record SignupRequest(
        @NotBlank String username,
        @NotBlank @Size(min = 8, max = 100) String password,
        @NotBlank @Email String email,
        @NotBlank String name
) {
}
