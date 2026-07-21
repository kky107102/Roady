package com.blockai.roadbuddy.user.dto;

import com.blockai.roadbuddy.user.domain.UserAccount;
import com.blockai.roadbuddy.user.domain.UserRole;

import java.time.LocalDateTime;

public record UserResponse(
        String id,
        String username,
        String name,
        UserRole role,
        boolean active,
        LocalDateTime createdAt
) {

    public static UserResponse from(UserAccount user) {
        return new UserResponse(
                user.id(),
                user.username(),
                user.name(),
                user.role(),
                user.active(),
                user.createdAt()
        );
    }
}
