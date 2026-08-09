package com.blockai.roady.damage.domain;

import java.math.BigDecimal;

public record DamageMapMarker(
        Long id,
        BigDecimal latitude,
        BigDecimal longitude,
        String currentStatus
) {
}
