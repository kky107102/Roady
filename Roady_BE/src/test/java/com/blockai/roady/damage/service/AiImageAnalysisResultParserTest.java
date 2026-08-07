package com.blockai.roady.damage.service;

import com.fasterxml.jackson.databind.json.JsonMapper;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;

class AiImageAnalysisResultParserTest {

    private final AiImageAnalysisResultParser parser = new AiImageAnalysisResultParser(JsonMapper.builder().build());

    @Test
    void parseReadsCamelCaseAiResponse() {
        ParsedAiImageAnalysisResult result = parser.parse("""
                {
                  "damaged": true,
                  "damageScore": 82,
                  "damageType": "CRACK",
                  "repairRequired": true,
                  "repairPriority": "HIGH",
                  "confidenceScore": 0.91
                }
                """);

        assertThat(result.damaged()).isTrue();
        assertThat(result.damageScore()).isEqualTo(82);
        assertThat(result.damageType()).isEqualTo("CRACK");
        assertThat(result.repairRequired()).isTrue();
        assertThat(result.repairPriority()).isEqualTo("HIGH");
        assertThat(result.confidenceScore()).isEqualByComparingTo(BigDecimal.valueOf(0.91));
    }

    @Test
    void parseReadsSnakeCaseAiResponse() {
        ParsedAiImageAnalysisResult result = parser.parse("""
                {
                  "damage_detected": true,
                  "damage_score": "71",
                  "damage_type": "마모",
                  "repair_required": "true",
                  "repair_priority": "URGENT",
                  "confidence": "0.875"
                }
                """);

        assertThat(result.damaged()).isTrue();
        assertThat(result.damageScore()).isEqualTo(71);
        assertThat(result.damageType()).isEqualTo("WEAR");
        assertThat(result.repairRequired()).isTrue();
        assertThat(result.repairPriority()).isEqualTo("URGENT");
        assertThat(result.confidenceScore()).isEqualByComparingTo(new BigDecimal("0.875"));
    }

    @Test
    void parseReadsFastApiContractAndIgnoresAnalysisDetail() {
        ParsedAiImageAnalysisResult result = parser.parse("""
                {
                  "damaged": true,
                  "damage_score": 45,
                  "damage_type": null,
                  "repair_required": true,
                  "repair_priority": "NORMAL",
                  "confidence_score": 0.8432,
                  "analysis_status": "COMPLETED",
                  "analysis_detail": {
                    "model": {"name": "yolo26s_seg_v1_best.pt"},
                    "images": [{"damage_ratio_percent": 8.5}]
                  }
                }
                """);

        assertThat(result.damaged()).isTrue();
        assertThat(result.damageScore()).isEqualTo(45);
        assertThat(result.damageType()).isNull();
        assertThat(result.repairRequired()).isTrue();
        assertThat(result.repairPriority()).isEqualTo("NORMAL");
        assertThat(result.confidenceScore()).isEqualByComparingTo(new BigDecimal("0.8432"));
    }

    @Test
    void parseNormalizesLegacyAiDamageTypes() {
        ParsedAiImageAnalysisResult missing = parser.parse("""
                {
                  "damageType": "MISSING"
                }
                """);
        ParsedAiImageAnalysisResult breakage = parser.parse("""
                {
                  "damageType": "BREAKAGE"
                }
                """);

        assertThat(missing.damageType()).isEqualTo("LARGE_MISSING");
        assertThat(breakage.damageType()).isEqualTo("SMALL_MISSING");
    }

    @Test
    void parseReadsV2DetectionIndependentlyFromDamageScore() {
        ParsedAiImageAnalysisResult result = parser.parse("""
                {
                  "damaged": true,
                  "damage_score": 0,
                  "damage_type": "CRACK",
                  "repair_required": false,
                  "repair_priority": null,
                  "confidence_score": 0.7139,
                  "analysis_detail": {
                    "schema_version": "2.0",
                    "summary": {
                      "damage_detected": true,
                      "dominant_damage_type": "crack",
                      "max_damage_ratio_percent": 0.12,
                      "review_required": true,
                      "review_reasons": [
                        {"code": "MODEL_QUALITY_GATE_NOT_MET", "message": "검토 필요"}
                      ]
                    }
                  }
                }
                """);

        assertThat(result.damaged()).isTrue();
        assertThat(result.damageScore()).isZero();
        assertThat(result.damageType()).isEqualTo("CRACK");
        assertThat(result.repairRequired()).isFalse();
        assertThat(result.repairPriority()).isNull();
        assertThat(result.confidenceScore()).isEqualByComparingTo(new BigDecimal("0.7139"));
    }

    @Test
    void parseReadsConservativeDecisionWhenMissingRatioIsUnavailable() {
        ParsedAiImageAnalysisResult result = parser.parse("""
                {
                  "damaged": true,
                  "damage_score": 31,
                  "damage_type": "LARGE_MISSING",
                  "repair_required": true,
                  "repair_priority": "NORMAL",
                  "confidence_score": 0.0879,
                  "analysis_detail": {
                    "schema_version": "2.0",
                    "damage_ratio_percent": null,
                    "estimated_severity": "moderate",
                    "review_required": true
                  }
                }
                """);

        assertThat(result.damaged()).isTrue();
        assertThat(result.damageScore()).isEqualTo(31);
        assertThat(result.damageType()).isEqualTo("LARGE_MISSING");
        assertThat(result.repairRequired()).isTrue();
        assertThat(result.repairPriority()).isEqualTo("NORMAL");
        assertThat(result.confidenceScore()).isEqualByComparingTo(new BigDecimal("0.0879"));
    }

    @Test
    void parsePreservesV2UnknownDecisionAsNull() {
        ParsedAiImageAnalysisResult result = parser.parse("""
                {
                  "damaged": null,
                  "damage_score": null,
                  "damage_type": null,
                  "repair_required": null,
                  "repair_priority": null,
                  "confidence_score": null,
                  "analysis_detail": {
                    "schema_version": "2.0",
                    "review_required": true
                  }
                }
                """);

        assertThat(result.damaged()).isNull();
        assertThat(result.damageScore()).isNull();
        assertThat(result.damageType()).isNull();
        assertThat(result.repairRequired()).isNull();
        assertThat(result.repairPriority()).isNull();
        assertThat(result.confidenceScore()).isNull();
    }

    @Test
    void parseReturnsEmptyResultForInvalidJson() {
        ParsedAiImageAnalysisResult result = parser.parse("not-json");

        assertThat(result.damaged()).isNull();
        assertThat(result.damageScore()).isNull();
        assertThat(result.damageType()).isNull();
        assertThat(result.repairRequired()).isNull();
        assertThat(result.repairPriority()).isNull();
        assertThat(result.confidenceScore()).isNull();
    }
}
