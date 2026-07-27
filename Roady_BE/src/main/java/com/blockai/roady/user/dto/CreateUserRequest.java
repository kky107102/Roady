package com.blockai.roady.user.dto;

import com.blockai.roady.user.domain.UserRole;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CreateUserRequest(
        @NotBlank String username,
        @NotBlank @Size(min = 8, max = 100) String password,
        @NotBlank @Email String email,
        @NotBlank String name,
        @NotNull UserRole role
) {
}
