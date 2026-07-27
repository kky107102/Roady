package com.blockai.roady.damage.service;

import java.math.BigDecimal;

public record ParsedAiImageAnalysisResult(
        Boolean damaged,
        Integer damageScore,
        Boolean repairRequired,
        String repairPriority,
        BigDecimal confidenceScore
) {

    public static ParsedAiImageAnalysisResult empty() {
        return new ParsedAiImageAnalysisResult(null, null, null, null, null);
    }
}
