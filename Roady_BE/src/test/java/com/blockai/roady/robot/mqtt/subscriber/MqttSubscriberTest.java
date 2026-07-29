package com.blockai.roady.robot.mqtt.subscriber;

import com.blockai.roady.robot.service.RobotLocationService;
import org.junit.jupiter.api.Test;
import org.springframework.integration.mqtt.support.MqttHeaders;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;

class MqttSubscriberTest {

    @Test
    void receivesTelemetryAndDelegatesLocationProcessing() {
        RobotLocationService robotLocationService = mock(RobotLocationService.class);
        MqttSubscriber subscriber = new MqttSubscriber(robotLocationService);
        String payload = """
                {
                  "latitude": 37.501,
                  "longitude": 127.039,
                  "batteryLevel": 82,
                  "operationStatus": "MOVING",
                  "connectionStatus": "CONNECTED",
                  "recordedAt": "2026-07-29T14:30:00"
                }
                """;
        Message<String> message = MessageBuilder.withPayload(payload)
                .setHeader(MqttHeaders.RECEIVED_TOPIC, "roady/10/telemetry")
                .build();

        subscriber.receive(message);

        verify(robotLocationService).saveLatest(10L, payload);
    }

    @Test
    void rejectsMalformedTopicBeforeProcessingPayload() {
        RobotLocationService robotLocationService = mock(RobotLocationService.class);
        MqttSubscriber subscriber = new MqttSubscriber(robotLocationService);
        Message<String> message = MessageBuilder.withPayload("{}")
                .setHeader(MqttHeaders.RECEIVED_TOPIC, "roady/robot-a/telemetry")
                .build();

        assertThatThrownBy(() -> subscriber.receive(message))
                .isInstanceOf(IllegalArgumentException.class);
        verifyNoInteractions(robotLocationService);
    }
}
