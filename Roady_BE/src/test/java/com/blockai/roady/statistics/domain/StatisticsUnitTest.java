package com.blockai.roady.statistics.domain;

import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class StatisticsUnitTest {

    @Test
    void floorsWeekToMonday() {
        LocalDateTime wednesday = LocalDateTime.of(2026, 7, 29, 15, 30);

        assertThat(StatisticsUnit.WEEK.floor(wednesday))
                .isEqualTo(LocalDateTime.of(2026, 7, 27, 0, 0));
    }

    @Test
    void rejectsUnknownUnit() {
        assertThatThrownBy(() -> StatisticsUnit.from("HOUR"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("unit must be one of DAY, WEEK, MONTH, YEAR.");
    }
}
