package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageSummary;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

public record DamageResponse(
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
                damage.addressName(),
                damage.roadAddressName(),
                damage.regionCode(),
                damage.region1DepthName(),
                damage.region2DepthName(),
                damage.region3DepthName(),
                damage.geocodedAt(),
                damage.latitude(),
                damage.longitude(),
                damage.capturedAt(),
                damage.currentStatus(),
                damage.processingPriority(),
                damage.imageCount(),
                images,
                damage.createdAt(),
                damage.updatedAt()
        );
    }
}
