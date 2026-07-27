package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageSummary;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record DamageSummaryResponse(
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

    public static DamageSummaryResponse from(DamageSummary damage) {
        return new DamageSummaryResponse(
                damage.id(),
                damage.robotId(),
                damage.reportedBy(),
                damage.assignedTo(),
                damage.description(),
                damage.latitude(),
                damage.longitude(),
                damage.capturedAt(),
                damage.currentStatus(),
                damage.imageCount(),
                damage.createdAt(),
                damage.updatedAt()
        );
    }
}
