package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotCommandStatus;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record UpdateRobotCommandStatusRequest(
        @NotNull RobotCommandStatus commandStatus,
        @Size(max = 1000) String resultMessage
) {
}
