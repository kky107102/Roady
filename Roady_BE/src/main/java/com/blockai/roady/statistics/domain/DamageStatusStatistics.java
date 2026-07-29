package com.blockai.roady.statistics.domain;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

public record DamageStatusStatistics(
        long totalCount,
        Map<String, Long> counts
) {

    public DamageStatusStatistics {
        counts = Collections.unmodifiableMap(new LinkedHashMap<>(counts));
    }
}
