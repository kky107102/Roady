package com.blockai.roady.damage.domain;

import java.util.Arrays;

public enum ReviewDamageType {
    LARGE_MISSING,
    SMALL_MISSING,
    WEAR,
    CRACK,
    OTHER;

    public static boolean contains(String value) {
        return Arrays.stream(values())
                .anyMatch(type -> type.name().equals(value));
    }
}
