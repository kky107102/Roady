package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotConnectionStatus;
import com.blockai.roady.robot.domain.RobotStatus;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record CreateRobotStatusLogRequest(
        @NotNull @DecimalMin("-90.0") @DecimalMax("90.0") BigDecimal latitude,
        @NotNull @DecimalMin("-180.0") @DecimalMax("180.0") BigDecimal longitude,
        @NotNull @Min(0) @Max(100) Integer batteryLevel,
        @NotNull RobotStatus operationStatus,
        @NotNull RobotConnectionStatus connectionStatus,
        @Size(max = 100) String errorCode,
        @Size(max = 500) String errorMessage,
        LocalDateTime recordedAt
) {
}
