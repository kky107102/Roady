package com.blockai.roady.damage.domain;

public record DamageStatusCount(
        String status,
        long total,
        long unassigned
) {
}
