package com.blockai.roady.damage.domain;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record DamageSummary(
        Long id,
        Long robotId,
        Long reportedBy,
        Long assignedTo,
        String description,
        String addressName,
        String roadAddressName,
        String regionCode,
        String region1DepthName,
        String region2DepthName,
        String region3DepthName,
        LocalDateTime geocodedAt,
        BigDecimal latitude,
        BigDecimal longitude,
        LocalDateTime capturedAt,
        String currentStatus,
        String processingPriority,
        long imageCount,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
}
