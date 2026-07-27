package com.blockai.roady.robot.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record RobotLatestStatusResponse(
        Long id,
        BigDecimal latitude,
        BigDecimal longitude,
        Integer batteryLevel,
        String operationStatus,
        String connectionStatus,
        String errorCode,
        String errorMessage,
        LocalDateTime recordedAt
) {
}
