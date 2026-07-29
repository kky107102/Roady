package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageSummary;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record DamageSearchItemResponse(
        Long id,
        Long robotId,
        Long assignedTo,
        String description,
        BigDecimal latitude,
        BigDecimal longitude,
        LocalDateTime capturedAt,
        String currentStatus,
        long imageCount,
        LocalDateTime createdAt
) {

    public static DamageSearchItemResponse from(DamageSummary damage) {
        return new DamageSearchItemResponse(
                damage.id(),
                damage.robotId(),
                damage.assignedTo(),
                damage.description(),
                damage.latitude(),
                damage.longitude(),
                damage.capturedAt(),
                damage.currentStatus(),
                damage.imageCount(),
                damage.createdAt()
        );
    }
}
