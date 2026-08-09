package com.blockai.roady.damage.domain;

import org.springframework.util.StringUtils;

import java.util.Locale;

public final class DamageTypeNormalizer {

    private DamageTypeNormalizer() {
    }

    public static String normalizeAiDamageType(String damageType) {
        if (!StringUtils.hasText(damageType)) {
            return null;
        }
        String normalized = damageType.trim().toUpperCase(Locale.ROOT);
        return switch (normalized) {
            case "MISSING", "LARGE_MISSING", "결손" -> "LARGE_MISSING";
            case "BREAKAGE", "BROKEN", "SMALL_MISSING", "깨짐" -> "SMALL_MISSING";
            case "WEAR", "마모" -> "WEAR";
            case "CRACK", "균열" -> "CRACK";
            default -> normalized;
        };
    }
}
