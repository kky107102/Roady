package com.blockai.roady.robot.domain;

import java.time.LocalDateTime;

public class RobotCommand {

    private Long id;
    private Long robotId;
    private Long requestedBy;
    private RobotCommandType commandType;
    private RobotCommandStatus commandStatus;
    private String resultMessage;
    private LocalDateTime requestedAt;
    private LocalDateTime completedAt;

    public RobotCommand() {
    }

    public RobotCommand(
            Long id,
            Long robotId,
            Long requestedBy,
            RobotCommandType commandType,
            RobotCommandStatus commandStatus,
            String resultMessage,
            LocalDateTime requestedAt,
            LocalDateTime completedAt
    ) {
        this.id = id;
        this.robotId = robotId;
        this.requestedBy = requestedBy;
        this.commandType = commandType;
        this.commandStatus = commandStatus;
        this.resultMessage = resultMessage;
        this.requestedAt = requestedAt;
        this.completedAt = completedAt;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getRobotId() {
        return robotId;
    }

    public void setRobotId(Long robotId) {
        this.robotId = robotId;
    }

    public Long getRequestedBy() {
        return requestedBy;
    }

    public void setRequestedBy(Long requestedBy) {
        this.requestedBy = requestedBy;
    }

    public RobotCommandType getCommandType() {
        return commandType;
    }

    public void setCommandType(RobotCommandType commandType) {
        this.commandType = commandType;
    }

    public RobotCommandStatus getCommandStatus() {
        return commandStatus;
    }

    public void setCommandStatus(RobotCommandStatus commandStatus) {
        this.commandStatus = commandStatus;
    }

    public String getResultMessage() {
        return resultMessage;
    }

    public void setResultMessage(String resultMessage) {
        this.resultMessage = resultMessage;
    }

    public LocalDateTime getRequestedAt() {
        return requestedAt;
    }

    public void setRequestedAt(LocalDateTime requestedAt) {
        this.requestedAt = requestedAt;
    }

    public LocalDateTime getCompletedAt() {
        return completedAt;
    }

    public void setCompletedAt(LocalDateTime completedAt) {
        this.completedAt = completedAt;
    }
}
