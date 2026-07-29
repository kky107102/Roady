package com.blockai.roady.statistics.dto;

import com.blockai.roady.statistics.domain.RepairPriorityStatistics;

import java.util.Map;

public record RepairPriorityStatisticsResponse(
        long totalCount,
        long classifiedCount,
        long unclassifiedCount,
        Map<String, Long> counts
) {

    public static RepairPriorityStatisticsResponse from(RepairPriorityStatistics statistics) {
        return new RepairPriorityStatisticsResponse(
                statistics.totalCount(),
                statistics.classifiedCount(),
                statistics.unclassifiedCount(),
                statistics.counts()
        );
    }
}
