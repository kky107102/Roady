package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotStatusLog;

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

    public static RobotLatestStatusResponse from(RobotStatusLog statusLog) {
        return new RobotLatestStatusResponse(
                statusLog.getId(),
                statusLog.getLatitude(),
                statusLog.getLongitude(),
                statusLog.getBatteryLevel(),
                statusLog.getOperationStatus().name(),
                statusLog.getConnectionStatus().name(),
                statusLog.getErrorCode(),
                statusLog.getErrorMessage(),
                statusLog.getRecordedAt()
        );
    }
}
