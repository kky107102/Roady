package com.blockai.roady.statistics.dto;

import com.blockai.roady.statistics.domain.DamageStatusStatistics;

import java.util.Map;

public record DamageStatusStatisticsResponse(
        long totalCount,
        Map<String, Long> counts
) {

    public static DamageStatusStatisticsResponse from(DamageStatusStatistics statistics) {
        return new DamageStatusStatisticsResponse(
                statistics.totalCount(),
                statistics.counts()
        );
    }
}
