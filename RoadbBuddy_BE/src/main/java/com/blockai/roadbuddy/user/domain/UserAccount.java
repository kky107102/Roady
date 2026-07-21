package com.blockai.roadbuddy.user.domain;

import java.time.LocalDateTime;
import java.util.UUID;

public record UserAccount(
        String id,
        String username,
        String password,
        String name,
        UserRole role,
        boolean active,
        LocalDateTime createdAt
) {

    public static UserAccount create(String username, String password, String name, UserRole role) {
        return new UserAccount(
                UUID.randomUUID().toString(),
                username,
                password,
                name,
                role,
                true,
                LocalDateTime.now()
        );
    }

    public UserAccount withRole(UserRole newRole) {
        return new UserAccount(id, username, password, name, newRole, active, createdAt);
    }

    public UserAccount withActive(boolean newActive) {
        return new UserAccount(id, username, password, name, role, newActive, createdAt);
    }
}
