package com.blockai.roadbuddy.user.dto;

import jakarta.validation.constraints.NotNull;

public record UpdateUserActiveRequest(
        @NotNull Boolean active
) {
}
