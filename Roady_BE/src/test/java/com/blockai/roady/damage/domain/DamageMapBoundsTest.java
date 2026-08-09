package com.blockai.roady.damage.domain;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DamageMapBoundsTest {

    @Test
    void rejectsOutOfRangeCoordinates() {
        assertThatThrownBy(() -> new DamageMapBounds(
                BigDecimal.valueOf(-91),
                BigDecimal.valueOf(37.62),
                BigDecimal.valueOf(126.80),
                BigDecimal.valueOf(127.10)
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Latitude must be between -90 and 90.");
    }

    @Test
    void rejectsReversedLongitudeBounds() {
        assertThatThrownBy(() -> new DamageMapBounds(
                BigDecimal.valueOf(37.45),
                BigDecimal.valueOf(37.62),
                BigDecimal.valueOf(127.10),
                BigDecimal.valueOf(126.80)
        ))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("west must be less than east.");
    }
}
