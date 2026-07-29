package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageSearchItem;

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
        Integer damageScore,
        Boolean repairRequired,
        String repairPriority,
        BigDecimal confidenceScore,
        LocalDateTime createdAt
) {

    public static DamageSearchItemResponse from(DamageSearchItem damage) {
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
                damage.damageScore(),
                damage.repairRequired(),
                damage.repairPriority(),
                damage.confidenceScore(),
                damage.createdAt()
        );
    }
}
