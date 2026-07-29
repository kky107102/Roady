package com.blockai.roady.robot.mqtt.event;

import com.blockai.roady.robot.domain.RobotCommand;
import com.blockai.roady.robot.mqtt.dto.RobotCommandMessage;

public record RobotCommandCreatedEvent(
        Long robotId,
        RobotCommandMessage message
) {
    public static RobotCommandCreatedEvent from(RobotCommand command) {
        return new RobotCommandCreatedEvent(
                command.getRobotId(),
                RobotCommandMessage.from(command)
        );
    }
}
