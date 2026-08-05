package com.blockai.roady.damage.dto;

import jakarta.validation.constraints.Size;

public record CreateDamageRepairRequest(
        String processingPriority,
        String reviewDamageType,
        Long repairerId,
        @Size(max = 1000, message = "note must be 1000 characters or less.")
        String note
) {
}
