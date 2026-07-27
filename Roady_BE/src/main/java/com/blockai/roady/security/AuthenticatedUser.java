package com.blockai.roady.security;

import com.blockai.roady.user.domain.UserRole;

public record AuthenticatedUser(
        Long id,
        String username,
        UserRole role
) {
}
