package com.blockai.roadbuddy.auth.dto;

import com.blockai.roadbuddy.security.AuthenticatedUser;
import com.blockai.roadbuddy.user.domain.UserRole;

public record MeResponse(
        String id,
        String username,
        UserRole role
) {

    public static MeResponse from(AuthenticatedUser user) {
        return new MeResponse(user.id(), user.username(), user.role());
    }
}
