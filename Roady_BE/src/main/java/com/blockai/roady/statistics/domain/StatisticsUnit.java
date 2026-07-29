package com.blockai.roady.statistics.domain;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.TemporalAdjusters;
import java.util.Locale;

public enum StatisticsUnit {
    DAY(DateTimeFormatter.ISO_LOCAL_DATE),
    WEEK(DateTimeFormatter.ISO_LOCAL_DATE),
    MONTH(DateTimeFormatter.ofPattern("yyyy-MM")),
    YEAR(DateTimeFormatter.ofPattern("yyyy"));

    private final DateTimeFormatter formatter;

    StatisticsUnit(DateTimeFormatter formatter) {
        this.formatter = formatter;
    }

    public static StatisticsUnit from(String value) {
        if (value == null) {
            throw new IllegalArgumentException("unit is required.");
        }
        try {
            return valueOf(value.toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            throw new IllegalArgumentException("unit must be one of DAY, WEEK, MONTH, YEAR.");
        }
    }

    public LocalDateTime floor(LocalDateTime value) {
        LocalDate date = value.toLocalDate();
        return switch (this) {
            case DAY -> date.atStartOfDay();
            case WEEK -> date.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY)).atStartOfDay();
            case MONTH -> date.withDayOfMonth(1).atStartOfDay();
            case YEAR -> date.withDayOfYear(1).atStartOfDay();
        };
    }

    public LocalDateTime next(LocalDateTime value) {
        return switch (this) {
            case DAY -> value.plusDays(1);
            case WEEK -> value.plusWeeks(1);
            case MONTH -> value.plusMonths(1);
            case YEAR -> value.plusYears(1);
        };
    }

    public String format(LocalDateTime value) {
        return formatter.format(value);
    }
}
