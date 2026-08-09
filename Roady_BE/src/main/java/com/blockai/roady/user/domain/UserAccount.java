package com.blockai.roady.user.domain;

import java.time.LocalDateTime;

public record UserAccount(
        Long id,
        String username,
        String password,
        String email,
        String name,
        String assignedRegionCode,
        UserRole role,
        boolean active,
        LocalDateTime createdAt
) {

    public UserAccount withRole(UserRole newRole) {
        return new UserAccount(
                id,
                username,
                password,
                email,
                name,
                assignedRegionCode,
                newRole,
                active,
                createdAt
        );
    }

    public UserAccount withActive(boolean newActive) {
        return new UserAccount(
                id,
                username,
                password,
                email,
                name,
                assignedRegionCode,
                role,
                newActive,
                createdAt
        );
    }

    public UserAccount withAssignedRegionCode(String newAssignedRegionCode) {
        return new UserAccount(
                id,
                username,
                password,
                email,
                name,
                newAssignedRegionCode,
                role,
                active,
                createdAt
        );
    }
}
