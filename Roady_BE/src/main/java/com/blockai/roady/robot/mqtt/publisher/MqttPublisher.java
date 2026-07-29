package com.blockai.roady.robot.mqtt.publisher;

import com.blockai.roady.robot.mqtt.RobotMqttTopics;
import com.blockai.roady.robot.mqtt.dto.RobotCommandMessage;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.integration.mqtt.support.MqttHeaders;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class MqttPublisher {

    private final MessageChannel mqttOutboundChannel;
    private final ObjectMapper objectMapper;

    /**
     * 로봇에게 제어 명령을 MQTT로 발행
     *
     * Topic :
     * roady/{robotId}/command
     */
    public void publishCommand(Long robotId, RobotCommandMessage command) {
        try {
            String topic = RobotMqttTopics.commandTopic(robotId);

            String payload = objectMapper.writeValueAsString(command);

            Message<String> message = MessageBuilder
                    .withPayload(payload)
                    .setHeader(MqttHeaders.TOPIC, topic)
                    .setHeader(MqttHeaders.QOS, 1)
                    .build();

            if (!mqttOutboundChannel.send(message)) {
                throw new IllegalStateException("MQTT outbound channel rejected robot command.");
            }

            log.info("Published robot command. robotId={}, commandId={}", robotId, command.commandId());
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("Failed to serialize robot command.", e);
        }
    }
}
