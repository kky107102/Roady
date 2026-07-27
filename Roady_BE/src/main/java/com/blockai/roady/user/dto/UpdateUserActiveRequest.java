package com.blockai.roady.user.dto;

import jakarta.validation.constraints.NotNull;

public record UpdateUserActiveRequest(
        @NotNull Boolean active
) {
}
