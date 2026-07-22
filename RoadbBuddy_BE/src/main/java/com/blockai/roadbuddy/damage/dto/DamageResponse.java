package com.blockai.roadbuddy.damage.dto;

import com.blockai.roadbuddy.damage.domain.DamageSummary;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

public record DamageResponse(
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
        List<DamageImageResponse> images,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {

    public static DamageResponse from(DamageSummary damage, List<DamageImageResponse> images) {
        return new DamageResponse(
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
                images,
                damage.createdAt(),
                damage.updatedAt()
        );
    }
}
