package com.blockai.roady.damage.service;

import com.blockai.roady.damage.domain.DamageTypeNormalizer;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;

@Component
public class AiImageAnalysisResultParser {

    private final ObjectMapper objectMapper;

    public AiImageAnalysisResultParser(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public ParsedAiImageAnalysisResult parse(String rawResult) {
        if (!StringUtils.hasText(rawResult)) {
            return ParsedAiImageAnalysisResult.empty();
        }

        try {
            JsonNode root = objectMapper.readTree(rawResult);
            return new ParsedAiImageAnalysisResult(
                    booleanValue(root, "damaged", "isDamaged", "damageDetected", "damage_detected"),
                    integerValue(root, "damageScore", "damage_score", "score"),
                    normalizeDamageType(textValue(root, "damageType", "damage_type", "type")),
                    booleanValue(root, "repairRequired", "repair_required"),
                    textValue(root, "repairPriority", "repair_priority"),
                    decimalValue(root, "confidenceScore", "confidence_score", "confidence")
            );
        } catch (Exception ex) {
            return ParsedAiImageAnalysisResult.empty();
        }
    }

    private Boolean booleanValue(JsonNode root, String... fieldNames) {
        JsonNode value = firstValue(root, fieldNames);
        if (value == null || value.isNull()) {
            return null;
        }
        if (value.isBoolean()) {
            return value.booleanValue();
        }
        if (value.isTextual()) {
            return Boolean.parseBoolean(value.textValue());
        }
        return null;
    }

    private Integer integerValue(JsonNode root, String... fieldNames) {
        JsonNode value = firstValue(root, fieldNames);
        if (value == null || value.isNull()) {
            return null;
        }
        if (value.isInt() || value.isLong()) {
            return value.intValue();
        }
        if (value.isNumber()) {
            return value.numberValue().intValue();
        }
        if (value.isTextual()) {
            try {
                return Integer.parseInt(value.textValue());
            } catch (NumberFormatException ex) {
                return null;
            }
        }
        return null;
    }

    private String textValue(JsonNode root, String... fieldNames) {
        JsonNode value = firstValue(root, fieldNames);
        if (value == null || value.isNull()) {
            return null;
        }
        return value.asText();
    }

    private String normalizeDamageType(String damageType) {
        return DamageTypeNormalizer.normalizeAiDamageType(damageType);
    }

    private BigDecimal decimalValue(JsonNode root, String... fieldNames) {
        JsonNode value = firstValue(root, fieldNames);
        if (value == null || value.isNull()) {
            return null;
        }
        if (value.isNumber()) {
            return value.decimalValue();
        }
        if (value.isTextual()) {
            try {
                return new BigDecimal(value.textValue());
            } catch (NumberFormatException ex) {
                return null;
            }
        }
        return null;
    }

    private JsonNode firstValue(JsonNode root, String... fieldNames) {
        for (String fieldName : fieldNames) {
            JsonNode value = root.path(fieldName);
            if (!value.isMissingNode()) {
                return value;
            }
        }
        return null;
    }
}
