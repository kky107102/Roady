package com.blockai.roady.robot.service;

import com.blockai.roady.robot.domain.RobotConnectionStatus;
import com.blockai.roady.robot.domain.RobotStatus;
import com.blockai.roady.robot.dto.RobotLocationState;
import com.blockai.roady.robot.redis.RobotLocationCache;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class RobotLocationServiceTest {

    private RobotLocationCache robotLocationCache;
    private RobotLocationService service;

    @BeforeEach
    void setUp() {
        ObjectMapper objectMapper = JsonMapper.builder()
                .findAndAddModules()
                .build();
        Validator validator = Validation.buildDefaultValidatorFactory().getValidator();
        robotLocationCache = mock(RobotLocationCache.class);
        service = new RobotLocationService(objectMapper, validator, robotLocationCache);
    }

    @Test
    void saveLatestStoresValidLocationPayloadIntoCache() {
        String payload = """
                {
                  "latitude": 37.501,
                  "longitude": 127.039,
                  "batteryLevel": 82,
                  "operationStatus": "MOVING",
                  "connectionStatus": "CONNECTED",
                  "recordedAt": "2026-07-28T14:30:00"
                }
                """;

        RobotLocationState state = service.saveLatest(10L, payload);

        ArgumentCaptor<RobotLocationState> captor = ArgumentCaptor.forClass(RobotLocationState.class);
        verify(robotLocationCache).saveLatest(captor.capture());

        assertThat(state).isEqualTo(captor.getValue());
        assertThat(state.robotId()).isEqualTo(10L);
        assertThat(state.latitude()).isEqualByComparingTo(BigDecimal.valueOf(37.501));
        assertThat(state.longitude()).isEqualByComparingTo(BigDecimal.valueOf(127.039));
        assertThat(state.batteryLevel()).isEqualTo(82);
        assertThat(state.operationStatus()).isEqualTo(RobotStatus.MOVING);
        assertThat(state.connectionStatus()).isEqualTo(RobotConnectionStatus.CONNECTED);
    }

    @Test
    void saveLatestRejectsInvalidPayload() {
        String payload = """
                {
                  "latitude": 100,
                  "longitude": 127.039,
                  "batteryLevel": 82,
                  "operationStatus": "MOVING",
                  "connectionStatus": "CONNECTED"
                }
                """;

        assertThatThrownBy(() -> service.saveLatest(10L, payload))
                .isInstanceOf(RuntimeException.class);
    }
}
