package com.blockai.roady.robot.service;

import com.blockai.roady.robot.domain.RobotCommand;
import com.blockai.roady.robot.domain.RobotCommandStatus;
import com.blockai.roady.robot.domain.RobotCommandType;
import com.blockai.roady.robot.mapper.RobotCommandMapper;
import com.blockai.roady.robot.mqtt.event.RobotCommandCreatedEvent;
import org.junit.jupiter.api.Test;
import org.springframework.context.ApplicationEventPublisher;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class RobotCommandServiceTest {

    @Test
    void createPublishesEventForPersistedCommand() {
        RobotCommandMapper mapper = mock(RobotCommandMapper.class);
        RobotService robotService = mock(RobotService.class);
        ApplicationEventPublisher eventPublisher = mock(ApplicationEventPublisher.class);
        RobotCommandService service = new RobotCommandService(mapper, robotService, eventPublisher);
        LocalDateTime requestedAt = LocalDateTime.of(2026, 7, 29, 14, 30);
        RobotCommand persisted = new RobotCommand(
                15L,
                10L,
                3L,
                RobotCommandType.START_PATROL,
                RobotCommandStatus.PENDING,
                null,
                requestedAt,
                null
        );
        doAnswer(invocation -> {
            invocation.<RobotCommand>getArgument(0).setId(15L);
            return 1;
        }).when(mapper).insert(any(RobotCommand.class));
        when(mapper.findById(15L)).thenReturn(persisted);

        RobotCommand result = service.create(10L, 3L, RobotCommandType.START_PATROL);

        assertThat(result).isSameAs(persisted);
        verify(robotService).get(10L);
        verify(eventPublisher).publishEvent(RobotCommandCreatedEvent.from(persisted));
    }

    @Test
    void updateStatusAcceptsDuplicateAckWithoutUpdatingAgain() {
        RobotCommandMapper mapper = mock(RobotCommandMapper.class);
        RobotService robotService = mock(RobotService.class);
        ApplicationEventPublisher eventPublisher = mock(ApplicationEventPublisher.class);
        RobotCommandService service = new RobotCommandService(mapper, robotService, eventPublisher);
        RobotCommand persisted = new RobotCommand(
                15L,
                10L,
                3L,
                RobotCommandType.START_PATROL,
                RobotCommandStatus.IN_PROGRESS,
                null,
                LocalDateTime.of(2026, 7, 29, 14, 30),
                null
        );
        when(mapper.findById(15L)).thenReturn(persisted);

        RobotCommand result = service.updateStatus(
                10L,
                15L,
                RobotCommandStatus.IN_PROGRESS,
                "Duplicate ACK"
        );

        assertThat(result).isSameAs(persisted);
        verify(mapper, never()).updateStatus(any(), any(), any(), any(), any());
    }
}
