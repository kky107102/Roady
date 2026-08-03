package com.blockai.roady.damage.domain;

import java.util.Arrays;

public enum DamageStatus {
    COLLECTED,
    AI_ANALYZING,
    AI_ANALYZED,
    REQUESTED,
    REPAIR_IN_PROGRESS,
    REPAIR_COMPLETED,
    CANCELED;

    public static boolean contains(String value) {
        return Arrays.stream(values())
                .anyMatch(status -> status.name().equals(value));
    }
}
