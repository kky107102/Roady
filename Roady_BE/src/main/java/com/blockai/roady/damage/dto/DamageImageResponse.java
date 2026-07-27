package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageImageMetadata;

import java.time.LocalDateTime;

public record DamageImageResponse(
        Long id,
        Long damageId,
        int sortOrder,
        String originalFilename,
        String contentType,
        long sizeBytes,
        LocalDateTime createdAt
) {

    public static DamageImageResponse from(DamageImageMetadata image) {
        return new DamageImageResponse(
                image.id(),
                image.damageId(),
                image.sortOrder(),
                image.originalFilename(),
                image.contentType(),
                image.sizeBytes(),
                image.createdAt()
        );
    }
}
