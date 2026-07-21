package com.blockai.roadbuddy.user.dto;

import com.blockai.roadbuddy.user.domain.UserRole;
import jakarta.validation.constraints.NotNull;

public record UpdateUserRoleRequest(
        @NotNull UserRole role
) {
}
