package com.blockai.roady.damage.domain;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

public record DamageDashboardSummary(
        long total,
        long unassigned,
        Map<String, Long> statusCounts
) {

    public DamageDashboardSummary {
        statusCounts = Collections.unmodifiableMap(new LinkedHashMap<>(statusCounts));
    }
}
