package com.blockai.roady.damage.dto;

import com.blockai.roady.damage.domain.DamageAiAnalysisResult;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record DamageAiAnalysisResponse(
        Long id,
        Long damageId,
        Boolean damaged,
        Integer damageScore,
        String damageType,
        Boolean repairRequired,
        String repairPriority,
        BigDecimal confidenceScore,
        String analysisStatus,
        String rawResult,
        LocalDateTime analyzedAt,
        LocalDateTime createdAt
) {

    public static DamageAiAnalysisResponse from(DamageAiAnalysisResult result) {
        return new DamageAiAnalysisResponse(
                result.getId(),
                result.getDamageId(),
                result.getDamaged(),
                result.getDamageScore(),
                result.getDamageType(),
                result.getRepairRequired(),
                result.getRepairPriority(),
                result.getConfidenceScore(),
                result.getAnalysisStatus(),
                result.getRawResult(),
                result.getAnalyzedAt(),
                result.getCreatedAt()
        );
    }
}
