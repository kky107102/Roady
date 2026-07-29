package com.blockai.roady.robot.mqtt.dto;

import com.blockai.roady.robot.domain.RobotCommand;
import com.blockai.roady.robot.domain.RobotCommandType;
import com.fasterxml.jackson.annotation.JsonFormat;

import java.time.LocalDateTime;

public record RobotCommandMessage(
        Long commandId,
        RobotCommandType commandType,
        @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
        LocalDateTime requestedAt
) {
    public static RobotCommandMessage from(RobotCommand command) {
        return new RobotCommandMessage(
                command.getId(),
                command.getCommandType(),
                command.getRequestedAt()
        );
    }
}
