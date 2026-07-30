package com.blockai.roady.damage.domain;

import java.time.LocalDateTime;

public record DamageFilterCriteria(
        LocalDateTime from,
        LocalDateTime to,
        String status,
        Long robotId,
        Long assignedTo,
        String regionCode
) {

    public DamageFilterCriteria {
        regionCode = normalize(regionCode);
        if (from != null && to != null && !from.isBefore(to)) {
            throw new IllegalArgumentException("from must be earlier than to.");
        }
        if (status != null && !DamageStatus.contains(status)) {
            throw new IllegalArgumentException("Invalid damage status.");
        }
    }

    public DamageFilterCriteria(
            LocalDateTime from,
            LocalDateTime to,
            String status,
            Long robotId,
            Long assignedTo
    ) {
        this(from, to, status, robotId, assignedTo, null);
    }

    private static String normalize(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }
}
