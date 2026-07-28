package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotCommand;

import java.time.LocalDateTime;

public record RobotCommandResponse(
        Long id,
        Long robotId,
        Long requestedBy,
        String commandType,
        String commandStatus,
        String resultMessage,
        LocalDateTime requestedAt,
        LocalDateTime completedAt
) {

    public static RobotCommandResponse from(RobotCommand command) {
        return new RobotCommandResponse(
                command.getId(),
                command.getRobotId(),
                command.getRequestedBy(),
                command.getCommandType().name(),
                command.getCommandStatus().name(),
                command.getResultMessage(),
                command.getRequestedAt(),
                command.getCompletedAt()
        );
    }
}
