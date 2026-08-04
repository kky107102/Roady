package com.blockai.roady.robot.service;

import com.blockai.roady.robot.config.RobotLocationProperties;
import com.blockai.roady.robot.dto.RobotLocationState;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

@Service
@Slf4j
public class RobotTelemetryPersistenceService {

    private final RobotStatusLogService robotStatusLogService;
    private final RobotLocationProperties properties;
    private final ConcurrentMap<Long, RobotLocationState> lastPersistedStates = new ConcurrentHashMap<>();

    public RobotTelemetryPersistenceService(
            RobotStatusLogService robotStatusLogService,
            RobotLocationProperties properties
    ) {
        this.robotStatusLogService = robotStatusLogService;
        this.properties = properties;
    }

    public void persistIfRequired(RobotLocationState state) {
        lastPersistedStates.compute(state.robotId(), (robotId, previousState) -> {
            if (!shouldPersist(previousState, state)) {
                return previousState;
            }

            try {
                robotStatusLogService.create(
                        state.robotId(),
                        state.latitude(),
                        state.longitude(),
                        state.batteryLevel(),
                        state.operationStatus(),
                        state.connectionStatus(),
                        state.errorCode(),
                        state.errorMessage(),
                        state.recordedAt()
                );
                return state;
            } catch (RuntimeException ex) {
                log.warn("Failed to persist robot telemetry. robotId={}", robotId, ex);
                return previousState;
            }
        });
    }

    private boolean shouldPersist(RobotLocationState previousState, RobotLocationState currentState) {
        return previousState == null
                || hasImportantStateChanged(previousState, currentState)
                || isPersistenceIntervalElapsed(previousState, currentState);
    }

    private boolean hasImportantStateChanged(
            RobotLocationState previousState,
            RobotLocationState currentState
    ) {
        return previousState.operationStatus() != currentState.operationStatus()
                || previousState.connectionStatus() != currentState.connectionStatus()
                || !Objects.equals(previousState.errorCode(), currentState.errorCode())
                || !Objects.equals(previousState.errorMessage(), currentState.errorMessage());
    }

    private boolean isPersistenceIntervalElapsed(
            RobotLocationState previousState,
            RobotLocationState currentState
    ) {
        Duration interval = properties.getRdbPersistenceInterval();
        if (interval == null || interval.isZero() || interval.isNegative()) {
            return true;
        }
        if (previousState.receivedAt() == null || currentState.receivedAt() == null) {
            return true;
        }
        return !currentState.receivedAt().isBefore(previousState.receivedAt().plus(interval));
    }
}
