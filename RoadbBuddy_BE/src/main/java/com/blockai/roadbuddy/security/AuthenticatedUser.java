package com.blockai.roadbuddy.security;

import com.blockai.roadbuddy.user.domain.UserRole;

public record AuthenticatedUser(
        Long id,
        String username,
        UserRole role
) {
}
