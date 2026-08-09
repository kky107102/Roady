package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageSearchPage;

import java.util.List;

public record DamageSearchResponse(
        List<DamageSearchItemResponse> content,
        int page,
        int size,
        long totalElements,
        long totalPages
) {

    public static DamageSearchResponse from(DamageSearchPage result) {
        return new DamageSearchResponse(
                result.content().stream()
                        .map(DamageSearchItemResponse::from)
                        .toList(),
                result.page(),
                result.size(),
                result.totalElements(),
                result.totalPages()
        );
    }
}
