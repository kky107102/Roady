package com.blockai.roady.auth.dto;

import com.blockai.roady.security.AuthenticatedUser;
import com.blockai.roady.user.domain.UserRole;

public record MeResponse(
        Long id,
        String username,
        UserRole role
) {

    public static MeResponse from(AuthenticatedUser user) {
        return new MeResponse(user.id(), user.username(), user.role());
    }
}
