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
