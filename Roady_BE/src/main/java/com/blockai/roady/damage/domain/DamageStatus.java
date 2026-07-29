package com.blockai.roady.damage.domain;

import java.util.Arrays;

public enum DamageStatus {
    COLLECTED,
    REVIEW_REQUIRED,
    RECEIVED,
    REPAIR_SCHEDULED,
    REPAIRING,
    REPAIR_COMPLETED,
    REPAIR_NOT_REQUIRED;

    public static boolean contains(String value) {
        return Arrays.stream(values())
                .anyMatch(status -> status.name().equals(value));
    }
}
