package com.blockai.roady.damage.domain;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record DamageSearchItem(
        Long id,
        Long robotId,
        Long assignedTo,
        String description,
        BigDecimal latitude,
        BigDecimal longitude,
        LocalDateTime capturedAt,
        String currentStatus,
        long imageCount,
        Integer damageScore,
        Boolean repairRequired,
        String repairPriority,
        BigDecimal confidenceScore,
        LocalDateTime createdAt
) {
}
