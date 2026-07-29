package com.blockai.roady.damage.domain;

import java.time.LocalDateTime;
import java.util.Set;

public record DamageSearchCriteria(
        LocalDateTime from,
        LocalDateTime to,
        String status,
        Long robotId,
        Long assignedTo,
        int page,
        int size
) {

    private static final int MAX_PAGE_SIZE = 100;
    private static final Set<String> STATUSES = Set.of(
            "COLLECTED",
            "REVIEW_REQUIRED",
            "RECEIVED",
            "REPAIR_SCHEDULED",
            "REPAIRING",
            "REPAIR_COMPLETED",
            "REPAIR_NOT_REQUIRED"
    );

    public DamageSearchCriteria {
        if (from != null && to != null && !from.isBefore(to)) {
            throw new IllegalArgumentException("from must be earlier than to.");
        }
        if (status != null && !STATUSES.contains(status)) {
            throw new IllegalArgumentException("Invalid damage status.");
        }
        if (page < 0) {
            throw new IllegalArgumentException("page must be 0 or greater.");
        }
        if (size < 1 || size > MAX_PAGE_SIZE) {
            throw new IllegalArgumentException("size must be between 1 and 100.");
        }
    }

    public long offset() {
        return (long) page * size;
    }
}
