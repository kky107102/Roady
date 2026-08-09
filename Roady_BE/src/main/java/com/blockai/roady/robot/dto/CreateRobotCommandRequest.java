package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotCommandType;
import jakarta.validation.constraints.NotNull;

public record CreateRobotCommandRequest(
        @NotNull RobotCommandType commandType
) {
}
