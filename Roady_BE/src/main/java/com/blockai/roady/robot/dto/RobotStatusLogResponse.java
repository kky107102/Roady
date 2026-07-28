package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotStatusLog;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record RobotStatusLogResponse(
        Long id,
        Long robotId,
        BigDecimal latitude,
        BigDecimal longitude,
        Integer batteryLevel,
        String operationStatus,
        String connectionStatus,
        String errorCode,
        String errorMessage,
        LocalDateTime recordedAt
) {

    public static RobotStatusLogResponse from(RobotStatusLog statusLog) {
        return new RobotStatusLogResponse(
                statusLog.getId(),
                statusLog.getRobotId(),
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
