package com.blockai.roady.statistics.domain;

public record DamageTimeSeriesRow(
        String period,
        long totalCount,
        long repairCompletedCount
) {
}
