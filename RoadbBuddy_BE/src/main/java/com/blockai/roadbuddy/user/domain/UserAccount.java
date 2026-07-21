package com.blockai.roadbuddy.user.domain;

import java.time.LocalDateTime;

public record UserAccount(
        Long id,
        String username,
        String password,
        String email,
        String name,
        UserRole role,
        boolean active,
        LocalDateTime createdAt
) {

    public UserAccount withRole(UserRole newRole) {
        return new UserAccount(id, username, password, email, name, newRole, active, createdAt);
    }

    public UserAccount withActive(boolean newActive) {
        return new UserAccount(id, username, password, email, name, role, newActive, createdAt);
    }
}
