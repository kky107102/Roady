package com.blockai.roady.robot.service;

import com.blockai.roady.robot.domain.RobotCommand;
import com.blockai.roady.robot.domain.RobotCommandStatus;
import com.blockai.roady.robot.mqtt.dto.RobotCommandAckMessage;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import jakarta.validation.Validator;
import org.springframework.stereotype.Service;

import java.util.Set;

@Service
public class RobotCommandAckService {

    private final ObjectMapper objectMapper;
    private final Validator validator;
    private final RobotCommandService robotCommandService;

    public RobotCommandAckService(
            ObjectMapper objectMapper,
            Validator validator,
            RobotCommandService robotCommandService
    ) {
        this.objectMapper = objectMapper;
        this.validator = validator;
        this.robotCommandService = robotCommandService;
    }

    public RobotCommand handle(Long robotId, String payload) {
        RobotCommandAckMessage message = deserialize(payload);
        validate(message);
        validateAckStatus(message.commandStatus());
        return robotCommandService.updateStatus(
                robotId,
                message.commandId(),
                message.commandStatus(),
                message.resultMessage()
        );
    }

    private RobotCommandAckMessage deserialize(String payload) {
        try {
            return objectMapper.readValue(payload, RobotCommandAckMessage.class);
        } catch (JsonProcessingException ex) {
            throw new IllegalArgumentException("Failed to deserialize robot command ACK.", ex);
        }
    }

    private void validate(RobotCommandAckMessage message) {
        Set<ConstraintViolation<RobotCommandAckMessage>> violations = validator.validate(message);
        if (!violations.isEmpty()) {
            throw new ConstraintViolationException(violations);
        }
    }

    private void validateAckStatus(RobotCommandStatus status) {
        if (status != RobotCommandStatus.IN_PROGRESS
                && status != RobotCommandStatus.SUCCEEDED
                && status != RobotCommandStatus.FAILED) {
            throw new IllegalArgumentException("Invalid robot command ACK status.");
        }
    }
}
