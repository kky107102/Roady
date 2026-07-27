package com.blockai.roady.user.dto;

import com.blockai.roady.user.domain.UserAccount;
import com.blockai.roady.user.domain.UserRole;

import java.time.LocalDateTime;

public record UserResponse(
        Long id,
        String username,
        String email,
        String name,
        UserRole role,
        boolean active,
        LocalDateTime createdAt
) {

    public static UserResponse from(UserAccount user) {
        return new UserResponse(
                user.id(),
                user.username(),
                user.email(),
                user.name(),
                user.role(),
                user.active(),
                user.createdAt()
        );
    }
}
