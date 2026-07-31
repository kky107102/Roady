package com.blockai.roady.damage.dto;

public record UpdateDamageReviewRequest(
        String status,
        String processingPriority
) {
}
