package com.blockai.roady.damage.domain;

import java.util.List;

public record DamageSearchPage(
        List<DamageSummary> content,
        int page,
        int size,
        long totalElements,
        long totalPages
) {

    public static DamageSearchPage of(
            List<DamageSummary> content,
            DamageSearchCriteria criteria,
            long totalElements
    ) {
        long totalPages = totalElements / criteria.size();
        if (totalElements % criteria.size() != 0) {
            totalPages++;
        }

        return new DamageSearchPage(
                List.copyOf(content),
                criteria.page(),
                criteria.size(),
                totalElements,
                totalPages
        );
    }
}
