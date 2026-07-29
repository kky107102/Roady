package com.blockai.roady.damage.domain;

import java.time.LocalDateTime;

public record DamageFilterCriteria(
        LocalDateTime from,
        LocalDateTime to,
        String status,
        Long robotId,
        Long assignedTo
) {

    public DamageFilterCriteria {
        if (from != null && to != null && !from.isBefore(to)) {
            throw new IllegalArgumentException("from must be earlier than to.");
        }
        if (status != null && !DamageStatus.contains(status)) {
            throw new IllegalArgumentException("Invalid damage status.");
        }
    }
}
