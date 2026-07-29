package com.blockai.roady.robot.service;

import com.blockai.roady.robot.domain.RobotCommandStatus;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;

class RobotCommandAckServiceTest {

    private final RobotCommandService robotCommandService = mock(RobotCommandService.class);
    private final ObjectMapper objectMapper = JsonMapper.builder().findAndAddModules().build();
    private final Validator validator = Validation.buildDefaultValidatorFactory().getValidator();
    private final RobotCommandAckService service =
            new RobotCommandAckService(objectMapper, validator, robotCommandService);

    @Test
    void handlesValidCommandAck() {
        service.handle(10L, """
                {
                  "commandId": 15,
                  "commandStatus": "SUCCEEDED",
                  "resultMessage": "Patrol started"
                }
                """);

        verify(robotCommandService).updateStatus(
                10L,
                15L,
                RobotCommandStatus.SUCCEEDED,
                "Patrol started"
        );
    }

    @Test
    void rejectsStatusThatRobotCannotAcknowledge() {
        assertThatThrownBy(() -> service.handle(10L, """
                {
                  "commandId": 15,
                  "commandStatus": "CANCELED"
                }
                """))
                .isInstanceOf(IllegalArgumentException.class);

        verifyNoInteractions(robotCommandService);
    }
}
