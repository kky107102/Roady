package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageStatus;
import jakarta.validation.constraints.NotNull;

public record UpdateDamageStatusRequest(
        @NotNull DamageStatus status,
        String comment
) {
}
