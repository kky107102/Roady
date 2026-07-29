package com.blockai.roady.robot.mqtt.subscriber;

import com.blockai.roady.robot.service.RobotCommandAckService;
import org.junit.jupiter.api.Test;
import org.springframework.integration.mqtt.support.MqttHeaders;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class MqttCommandAckSubscriberTest {

    @Test
    void receivesAckAndDelegatesCommandUpdate() {
        RobotCommandAckService service = mock(RobotCommandAckService.class);
        MqttCommandAckSubscriber subscriber = new MqttCommandAckSubscriber(service);
        String payload = """
                {
                  "commandId": 15,
                  "commandStatus": "IN_PROGRESS",
                  "resultMessage": "Command accepted"
                }
                """;
        Message<String> message = MessageBuilder.withPayload(payload)
                .setHeader(MqttHeaders.RECEIVED_TOPIC, "roady/10/command/ack")
                .build();

        subscriber.receive(message);

        verify(service).handle(10L, payload);
    }
}
