package com.blockai.roady.robot.mqtt.dto;

import com.blockai.roady.robot.domain.RobotCommandStatus;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

public record RobotCommandAckMessage(
        @NotNull @Positive Long commandId,
        @NotNull RobotCommandStatus commandStatus,
        @Size(max = 1000) String resultMessage
) {
}
