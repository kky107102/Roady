package com.blockai.roady.damage.domain;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record DamageSummary(
        Long id,
        Long robotId,
        Long reportedBy,
        Long assignedTo,
        String description,
        BigDecimal latitude,
        BigDecimal longitude,
        LocalDateTime capturedAt,
        String currentStatus,
        long imageCount,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
}
