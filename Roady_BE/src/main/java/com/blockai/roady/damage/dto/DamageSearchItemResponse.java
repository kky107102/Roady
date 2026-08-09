package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageSearchItem;
import com.blockai.roady.damage.domain.DamageTypeNormalizer;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record DamageSearchItemResponse(
        Long id,
        Long robotId,
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
        String reviewDamageType,
        String reviewNote,
        long imageCount,
        Integer damageScore,
        String damageType,
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
                damage.reviewDamageType(),
                damage.reviewNote(),
                damage.imageCount(),
                damage.damageScore(),
                DamageTypeNormalizer.normalizeAiDamageType(damage.damageType()),
                damage.repairRequired(),
                damage.repairPriority(),
                damage.confidenceScore(),
                damage.createdAt()
        );
    }
}
