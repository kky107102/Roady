package com.blockai.roady.robot.mqtt.listener;

import com.blockai.roady.robot.domain.RobotCommandType;
import com.blockai.roady.robot.mqtt.dto.RobotCommandMessage;
import com.blockai.roady.robot.mqtt.event.RobotCommandCreatedEvent;
import com.blockai.roady.robot.mqtt.publisher.MqttPublisher;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class RobotCommandMqttListenerTest {

    @Test
    void publishesCreatedCommandAfterEventIsHandled() {
        MqttPublisher mqttPublisher = mock(MqttPublisher.class);
        RobotCommandMqttListener listener = new RobotCommandMqttListener(mqttPublisher);
        RobotCommandMessage message = new RobotCommandMessage(
                15L,
                RobotCommandType.START_PATROL,
                LocalDateTime.of(2026, 7, 29, 14, 30)
        );

        listener.publishCommand(new RobotCommandCreatedEvent(10L, message));

        verify(mqttPublisher).publishCommand(10L, message);
    }
}
