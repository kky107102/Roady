package com.blockai.roady.robot.service;

import com.blockai.roady.robot.dto.CreateRobotStatusLogRequest;
import com.blockai.roady.robot.dto.RobotLocationState;
import com.blockai.roady.robot.redis.RobotLocationCache;
import com.blockai.roady.robot.websocket.RobotLocationPublisher;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import jakarta.validation.Validator;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.Set;

@Service
public class RobotLocationService {

    private final ObjectMapper objectMapper;
    private final Validator validator;
    private final RobotLocationCache robotLocationCache;
    private final RobotLocationPublisher robotLocationPublisher;

    public RobotLocationService(
            ObjectMapper objectMapper,
            Validator validator,
            RobotLocationCache robotLocationCache,
            RobotLocationPublisher robotLocationPublisher
    ) {
        this.objectMapper = objectMapper;
        this.validator = validator;
        this.robotLocationCache = robotLocationCache;
        this.robotLocationPublisher = robotLocationPublisher;
    }

    public RobotLocationState saveLatest(Long robotId, String payload) {
        if (robotId == null || robotId <= 0) {
            throw new IllegalArgumentException("Robot id must be positive.");
        }

        CreateRobotStatusLogRequest request = deserialize(payload);
        return saveLatest(robotId, request);
    }

    public RobotLocationState saveLatest(Long robotId, CreateRobotStatusLogRequest request) {
        if (robotId == null || robotId <= 0) {
            throw new IllegalArgumentException("Robot id must be positive.");
        }

        validate(request);

        RobotLocationState state = RobotLocationState.from(robotId, request, LocalDateTime.now());
        robotLocationCache.saveLatest(state);
        robotLocationPublisher.publish(state);
        return state;
    }

    public Optional<RobotLocationState> findLatest(Long robotId) {
        if (robotId == null || robotId <= 0) {
            throw new IllegalArgumentException("Robot id must be positive.");
        }
        return robotLocationCache.findLatest(robotId);
    }

    private CreateRobotStatusLogRequest deserialize(String payload) {
        try {
            return objectMapper.readValue(payload, CreateRobotStatusLogRequest.class);
        } catch (JsonProcessingException ex) {
            throw new IllegalArgumentException("Failed to deserialize robot location payload.", ex);
        }
    }

    private void validate(CreateRobotStatusLogRequest request) {
        Set<ConstraintViolation<CreateRobotStatusLogRequest>> violations = validator.validate(request);
        if (!violations.isEmpty()) {
            throw new ConstraintViolationException(violations);
        }
    }
}
