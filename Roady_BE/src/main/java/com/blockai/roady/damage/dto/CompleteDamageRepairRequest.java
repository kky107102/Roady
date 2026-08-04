package com.blockai.roady.damage.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public record CompleteDamageRepairRequest(
        @NotNull(message = "completedAt is required.")
        LocalDate completedAt,
        @Size(max = 1000, message = "note must be 1000 characters or less.")
        String note
) {
}
