package com.blockai.roady.statistics.domain;

public record RepairCompletionCounts(
        long totalCount,
        long completedCount,
        long notRequiredCount
) {
}
