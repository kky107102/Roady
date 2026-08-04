package com.blockai.roady.robot.service;

import com.blockai.roady.robot.config.RobotLocationProperties;
import com.blockai.roady.robot.domain.RobotConnectionStatus;
import com.blockai.roady.robot.domain.RobotStatus;
import com.blockai.roady.robot.dto.RobotLocationState;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class RobotTelemetryPersistenceServiceTest {

    private RobotStatusLogService robotStatusLogService;
    private RobotTelemetryPersistenceService service;

    @BeforeEach
    void setUp() {
        RobotLocationProperties properties = new RobotLocationProperties();
        properties.setRdbPersistenceInterval(Duration.ofMinutes(1));
        robotStatusLogService = mock(RobotStatusLogService.class);
        service = new RobotTelemetryPersistenceService(robotStatusLogService, properties);
    }

    @Test
    void persistsFirstTelemetryImmediately() {
        LocalDateTime receivedAt = LocalDateTime.of(2026, 8, 4, 10, 0);

        service.persistIfRequired(state(receivedAt, RobotStatus.MOVING,
                RobotConnectionStatus.CONNECTED, null, null));

        verify(robotStatusLogService).create(
                10L,
                BigDecimal.valueOf(37.501),
                BigDecimal.valueOf(127.039),
                82,
                RobotStatus.MOVING,
                RobotConnectionStatus.CONNECTED,
                null,
                null,
                receivedAt.minusSeconds(1)
        );
    }

    @Test
    void skipsUnchangedTelemetryWithinPersistenceInterval() {
        service.persistIfRequired(state(LocalDateTime.of(2026, 8, 4, 10, 0), RobotStatus.MOVING,
                RobotConnectionStatus.CONNECTED, null, null));
        service.persistIfRequired(state(LocalDateTime.of(2026, 8, 4, 10, 0, 30), RobotStatus.MOVING,
                RobotConnectionStatus.CONNECTED, null, null));

        verifyCreateCalled(times(1));
    }

    @Test
    void persistsTelemetryWhenPersistenceIntervalElapses() {
        service.persistIfRequired(state(LocalDateTime.of(2026, 8, 4, 10, 0), RobotStatus.MOVING,
                RobotConnectionStatus.CONNECTED, null, null));
        service.persistIfRequired(state(LocalDateTime.of(2026, 8, 4, 10, 1), RobotStatus.MOVING,
                RobotConnectionStatus.CONNECTED, null, null));

        verifyCreateCalled(times(2));
    }

    @Test
    void persistsImportantStateChangesImmediately() {
        service.persistIfRequired(state(LocalDateTime.of(2026, 8, 4, 10, 0), RobotStatus.MOVING,
                RobotConnectionStatus.CONNECTED, null, null));
        service.persistIfRequired(state(LocalDateTime.of(2026, 8, 4, 10, 0, 5), RobotStatus.STOPPED,
                RobotConnectionStatus.CONNECTED, null, null));
        service.persistIfRequired(state(LocalDateTime.of(2026, 8, 4, 10, 0, 10), RobotStatus.STOPPED,
                RobotConnectionStatus.DISCONNECTED, null, null));
        service.persistIfRequired(state(LocalDateTime.of(2026, 8, 4, 10, 0, 15), RobotStatus.STOPPED,
                RobotConnectionStatus.DISCONNECTED, "MOTOR-001", "Motor stalled"));

        verifyCreateCalled(times(4));
    }

    @Test
    void persistsErrorMessageChangeImmediately() {
        service.persistIfRequired(state(LocalDateTime.of(2026, 8, 4, 10, 0), RobotStatus.ERROR,
                RobotConnectionStatus.CONNECTED, "MOTOR-001", "Motor stalled"));
        service.persistIfRequired(state(LocalDateTime.of(2026, 8, 4, 10, 0, 5), RobotStatus.ERROR,
                RobotConnectionStatus.CONNECTED, "MOTOR-001", "Motor overheated"));

        verifyCreateCalled(times(2));
    }

    @Test
    void retriesAfterDatabaseFailureWithoutInterruptingTelemetryProcessing() {
        when(robotStatusLogService.create(any(), any(), any(), any(), any(), any(), any(), any(), any()))
                .thenThrow(new IllegalStateException("database unavailable"))
                .thenReturn(null);
        RobotLocationState first = state(LocalDateTime.of(2026, 8, 4, 10, 0), RobotStatus.MOVING,
                RobotConnectionStatus.CONNECTED, null, null);
        RobotLocationState retry = state(LocalDateTime.of(2026, 8, 4, 10, 0, 5), RobotStatus.MOVING,
                RobotConnectionStatus.CONNECTED, null, null);

        assertThatCode(() -> service.persistIfRequired(first)).doesNotThrowAnyException();
        service.persistIfRequired(retry);

        verifyCreateCalled(times(2));
    }

    private RobotLocationState state(
            LocalDateTime receivedAt,
            RobotStatus operationStatus,
            RobotConnectionStatus connectionStatus,
            String errorCode,
            String errorMessage
    ) {
        return new RobotLocationState(
                10L,
                BigDecimal.valueOf(37.501),
                BigDecimal.valueOf(127.039),
                82,
                operationStatus,
                connectionStatus,
                errorCode,
                errorMessage,
                receivedAt.minusSeconds(1),
                receivedAt
        );
    }

    private void verifyCreateCalled(org.mockito.verification.VerificationMode mode) {
        verify(robotStatusLogService, mode).create(
                any(), any(), any(), any(), any(), any(), any(), any(), any()
        );
    }
}
