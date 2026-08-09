package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageMapMarker;

import java.math.BigDecimal;

public record DamageMapMarkerResponse(
        Long id,
        BigDecimal latitude,
        BigDecimal longitude,
        String currentStatus
) {

    public static DamageMapMarkerResponse from(DamageMapMarker marker) {
        return new DamageMapMarkerResponse(
                marker.id(),
                marker.latitude(),
                marker.longitude(),
                marker.currentStatus()
        );
    }
}
