package com.blockai.roady.damage.geocoding;

import java.time.LocalDateTime;

public record GeocodedAddress(
        String addressName,
        String roadAddressName,
        String region1DepthName,
        String region2DepthName,
        String region3DepthName,
        LocalDateTime geocodedAt
) {
}
