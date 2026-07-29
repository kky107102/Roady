package com.blockai.roady.damage.domain;

import java.time.LocalDateTime;
import java.util.Objects;

public record DamageSearchCriteria(
        DamageFilterCriteria filter,
        int page,
        int size
) {

    private static final int MAX_PAGE_SIZE = 100;

    public DamageSearchCriteria {
        Objects.requireNonNull(filter, "filter must not be null.");
        if (page < 0) {
            throw new IllegalArgumentException("page must be 0 or greater.");
        }
        if (size < 1 || size > MAX_PAGE_SIZE) {
            throw new IllegalArgumentException("size must be between 1 and 100.");
        }
    }

    public DamageSearchCriteria(
            LocalDateTime from,
            LocalDateTime to,
            String status,
            Long robotId,
            Long assignedTo,
            int page,
            int size
    ) {
        this(new DamageFilterCriteria(from, to, status, robotId, assignedTo), page, size);
    }

    public LocalDateTime from() {
        return filter.from();
    }

    public LocalDateTime to() {
        return filter.to();
    }

    public String status() {
        return filter.status();
    }

    public Long robotId() {
        return filter.robotId();
    }

    public Long assignedTo() {
        return filter.assignedTo();
    }

    public long offset() {
        return (long) page * size;
    }
}
