package com.blockai.roady.robot.mqtt.publisher;

import com.blockai.roady.robot.domain.RobotCommandType;
import com.blockai.roady.robot.mqtt.dto.RobotCommandMessage;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.integration.mqtt.support.MqttHeaders;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class MqttPublisherTest {

    @Test
    void publishesCommandWithCorrelationFields() throws Exception {
        MessageChannel channel = mock(MessageChannel.class);
        when(channel.send(any())).thenReturn(true);
        ObjectMapper objectMapper = JsonMapper.builder().findAndAddModules().build();
        MqttPublisher publisher = new MqttPublisher(channel, objectMapper);
        LocalDateTime requestedAt = LocalDateTime.of(2026, 7, 29, 14, 30);

        publisher.publishCommand(
                10L,
                new RobotCommandMessage(15L, RobotCommandType.START_PATROL, requestedAt)
        );

        ArgumentCaptor<Message<?>> captor = ArgumentCaptor.forClass(Message.class);
        verify(channel).send(captor.capture());
        Message<?> message = captor.getValue();
        assertThat(message.getHeaders().get(MqttHeaders.TOPIC)).isEqualTo("roady/10/command");
        assertThat(objectMapper.readTree((String) message.getPayload()))
                .isEqualTo(objectMapper.readTree("""
                        {
                          "commandId": 15,
                          "commandType": "START_PATROL",
                          "requestedAt": "2026-07-29T14:30:00"
                        }
                        """));
    }
}
