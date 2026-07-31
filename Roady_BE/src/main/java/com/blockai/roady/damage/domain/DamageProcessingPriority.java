package com.blockai.roady.damage.domain;

import java.util.Arrays;

public enum DamageProcessingPriority {
    LOW,
    NORMAL,
    HIGH,
    URGENT;

    public static boolean contains(String value) {
        return Arrays.stream(values())
                .anyMatch(priority -> priority.name().equals(value));
    }
}
