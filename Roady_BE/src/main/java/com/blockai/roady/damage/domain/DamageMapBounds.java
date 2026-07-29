package com.blockai.roady.damage.domain;

import java.math.BigDecimal;

public record DamageMapBounds(
        BigDecimal south,
        BigDecimal north,
        BigDecimal west,
        BigDecimal east
) {

    private static final BigDecimal MIN_LATITUDE = BigDecimal.valueOf(-90);
    private static final BigDecimal MAX_LATITUDE = BigDecimal.valueOf(90);
    private static final BigDecimal MIN_LONGITUDE = BigDecimal.valueOf(-180);
    private static final BigDecimal MAX_LONGITUDE = BigDecimal.valueOf(180);

    public DamageMapBounds {
        if (south == null || north == null || west == null || east == null) {
            throw new IllegalArgumentException("Map bounds are required.");
        }
        if (south.compareTo(MIN_LATITUDE) < 0 || north.compareTo(MAX_LATITUDE) > 0) {
            throw new IllegalArgumentException("Latitude must be between -90 and 90.");
        }
        if (west.compareTo(MIN_LONGITUDE) < 0 || east.compareTo(MAX_LONGITUDE) > 0) {
            throw new IllegalArgumentException("Longitude must be between -180 and 180.");
        }
        if (south.compareTo(north) >= 0) {
            throw new IllegalArgumentException("south must be less than north.");
        }
        if (west.compareTo(east) >= 0) {
            throw new IllegalArgumentException("west must be less than east.");
        }
    }
}
