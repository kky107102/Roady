package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageDashboardSummary;

import java.util.Map;

public record DamageDashboardSummaryResponse(
        long total,
        long unassigned,
        Map<String, Long> statusCounts
) {

    public static DamageDashboardSummaryResponse from(DamageDashboardSummary summary) {
        return new DamageDashboardSummaryResponse(
                summary.total(),
                summary.unassigned(),
                summary.statusCounts()
        );
    }
}
