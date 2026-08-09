package com.blockai.roady.statistics.domain;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

public record RepairPriorityStatistics(
        long totalCount,
        long classifiedCount,
        long unclassifiedCount,
        Map<String, Long> counts
) {

    public RepairPriorityStatistics {
        counts = Collections.unmodifiableMap(new LinkedHashMap<>(counts));
    }
}
