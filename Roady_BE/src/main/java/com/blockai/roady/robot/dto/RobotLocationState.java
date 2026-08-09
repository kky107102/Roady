package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotConnectionStatus;
import com.blockai.roady.robot.domain.RobotStatus;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record RobotLocationState(
        Long robotId,
        BigDecimal latitude,
        BigDecimal longitude,
        Integer batteryLevel,
        RobotStatus operationStatus,
        RobotConnectionStatus connectionStatus,
        String errorCode,
        String errorMessage,
        LocalDateTime recordedAt,
        LocalDateTime receivedAt
) {
    public static RobotLocationState from(
            Long robotId,
            CreateRobotStatusLogRequest request,
            LocalDateTime receivedAt
    ) {
        return new RobotLocationState(
                robotId,
                request.latitude(),
                request.longitude(),
                request.batteryLevel(),
                request.operationStatus(),
                request.connectionStatus(),
                request.errorCode(),
                request.errorMessage(),
                request.recordedAt(),
                receivedAt
        );
    }
}
