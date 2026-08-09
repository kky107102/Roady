package com.blockai.roady.robot.domain;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class RobotStatusLog {

    private Long id;
    private Long robotId;
    private BigDecimal latitude;
    private BigDecimal longitude;
    private Integer batteryLevel;
    private RobotStatus operationStatus;
    private RobotConnectionStatus connectionStatus;
    private String errorCode;
    private String errorMessage;
    private LocalDateTime recordedAt;

    public RobotStatusLog() {
    }

    public RobotStatusLog(
            Long id,
            Long robotId,
            BigDecimal latitude,
            BigDecimal longitude,
            Integer batteryLevel,
            RobotStatus operationStatus,
            RobotConnectionStatus connectionStatus,
            String errorCode,
            String errorMessage,
            LocalDateTime recordedAt
    ) {
        this.id = id;
        this.robotId = robotId;
        this.latitude = latitude;
        this.longitude = longitude;
        this.batteryLevel = batteryLevel;
        this.operationStatus = operationStatus;
        this.connectionStatus = connectionStatus;
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
        this.recordedAt = recordedAt;
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

    public BigDecimal getLatitude() {
        return latitude;
    }

    public void setLatitude(BigDecimal latitude) {
        this.latitude = latitude;
    }

    public BigDecimal getLongitude() {
        return longitude;
    }

    public void setLongitude(BigDecimal longitude) {
        this.longitude = longitude;
    }

    public Integer getBatteryLevel() {
        return batteryLevel;
    }

    public void setBatteryLevel(Integer batteryLevel) {
        this.batteryLevel = batteryLevel;
    }

    public RobotStatus getOperationStatus() {
        return operationStatus;
    }

    public void setOperationStatus(RobotStatus operationStatus) {
        this.operationStatus = operationStatus;
    }

    public RobotConnectionStatus getConnectionStatus() {
        return connectionStatus;
    }

    public void setConnectionStatus(RobotConnectionStatus connectionStatus) {
        this.connectionStatus = connectionStatus;
    }

    public String getErrorCode() {
        return errorCode;
    }

    public void setErrorCode(String errorCode) {
        this.errorCode = errorCode;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public LocalDateTime getRecordedAt() {
        return recordedAt;
    }

    public void setRecordedAt(LocalDateTime recordedAt) {
        this.recordedAt = recordedAt;
    }
}
