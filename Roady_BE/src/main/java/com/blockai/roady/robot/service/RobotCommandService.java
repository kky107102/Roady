package com.blockai.roady.robot.service;

import com.blockai.roady.robot.domain.RobotCommand;
import com.blockai.roady.robot.domain.RobotCommandStatus;
import com.blockai.roady.robot.domain.RobotCommandType;
import com.blockai.roady.robot.mapper.RobotCommandMapper;
import com.blockai.roady.robot.mqtt.event.RobotCommandCreatedEvent;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
public class RobotCommandService {

    private final RobotCommandMapper robotCommandMapper;
    private final RobotService robotService;
    private final ApplicationEventPublisher eventPublisher;

    public RobotCommandService(
            RobotCommandMapper robotCommandMapper,
            RobotService robotService,
            ApplicationEventPublisher eventPublisher
    ) {
        this.robotCommandMapper = robotCommandMapper;
        this.robotService = robotService;
        this.eventPublisher = eventPublisher;
    }

    @Transactional
    public RobotCommand create(Long robotId, Long requestedBy, RobotCommandType commandType) {
        robotService.get(robotId);

        RobotCommand command = new RobotCommand();
        command.setRobotId(robotId);
        command.setRequestedBy(requestedBy);
        command.setCommandType(commandType);
        command.setCommandStatus(RobotCommandStatus.PENDING);
        robotCommandMapper.insert(command);

        RobotCommand createdCommand = Optional.ofNullable(robotCommandMapper.findById(command.getId()))
                .orElseThrow(() -> new IllegalStateException("Created robot command not found."));
        eventPublisher.publishEvent(RobotCommandCreatedEvent.from(createdCommand));
        return createdCommand;
    }

    @Transactional(readOnly = true)
    public List<RobotCommand> findByRobotId(Long robotId) {
        robotService.get(robotId);
        return robotCommandMapper.findByRobotId(robotId);
    }

    @Transactional(readOnly = true)
    public List<RobotCommand> findPendingByRobotId(Long robotId) {
        robotService.get(robotId);
        return robotCommandMapper.findPendingByRobotId(robotId);
    }

    @Transactional
    public RobotCommand updateStatus(
            Long robotId,
            Long commandId,
            RobotCommandStatus commandStatus,
            String resultMessage
    ) {
        robotService.get(robotId);
        RobotCommand command = getByRobotId(robotId, commandId);
        validateStatusTransition(command.getCommandStatus(), commandStatus);

        LocalDateTime completedAt = isTerminal(commandStatus) ? LocalDateTime.now() : null;
        int updatedRows = robotCommandMapper.updateStatus(
                commandId,
                robotId,
                commandStatus,
                resultMessage,
                completedAt
        );
        if (updatedRows == 0) {
            throw new IllegalArgumentException("Robot command not found.");
        }

        return getByRobotId(robotId, commandId);
    }

    private RobotCommand getByRobotId(Long robotId, Long commandId) {
        RobotCommand command = Optional.ofNullable(robotCommandMapper.findById(commandId))
                .orElseThrow(() -> new IllegalArgumentException("Robot command not found."));
        if (!command.getRobotId().equals(robotId)) {
            throw new IllegalArgumentException("Robot command not found.");
        }
        return command;
    }

    private boolean isTerminal(RobotCommandStatus commandStatus) {
        return commandStatus == RobotCommandStatus.SUCCEEDED
                || commandStatus == RobotCommandStatus.FAILED
                || commandStatus == RobotCommandStatus.CANCELED;
    }

    private void validateStatusTransition(RobotCommandStatus currentStatus, RobotCommandStatus nextStatus) {
        if (currentStatus == RobotCommandStatus.PENDING) {
            if (nextStatus == RobotCommandStatus.IN_PROGRESS || nextStatus == RobotCommandStatus.CANCELED) {
                return;
            }
        }
        if (currentStatus == RobotCommandStatus.IN_PROGRESS) {
            if (isTerminal(nextStatus)) {
                return;
            }
        }
        throw new IllegalArgumentException("Invalid robot command status transition.");
    }
}
