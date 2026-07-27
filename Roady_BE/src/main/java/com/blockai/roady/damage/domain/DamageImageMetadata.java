package com.blockai.roady.damage.domain;

import java.time.LocalDateTime;

public record DamageImageMetadata(
        Long id,
        Long damageId,
        int sortOrder,
        String originalFilename,
        String contentType,
        long sizeBytes,
        LocalDateTime createdAt
) {
}
