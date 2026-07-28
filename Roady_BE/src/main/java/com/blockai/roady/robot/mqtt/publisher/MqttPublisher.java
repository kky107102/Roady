package com.blockai.roady.robot.mqtt.publisher;

import com.blockai.roady.robot.dto.CreateRobotCommandRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.integration.mqtt.support.MqttHeaders;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class MqttPublisher {

    private final MessageChannel mqttOutboundChannel;
    private final ObjectMapper objectMapper;

    /**
     * 로봇에게 제어 명령을 MQTT로 발행
     *
     * Topic :
     * roady/{robotId}/command
     */
    public void publishCommand(Long robotId,
                               CreateRobotCommandRequest request
    ) {
        try {
            String topic = "roady/" + robotId + "/command";

            String payload = objectMapper.writeValueAsString(request);

            Message<String> message = MessageBuilder
                    .withPayload(payload)
                    .setHeader(MqttHeaders.TOPIC, topic)
                    .setHeader(MqttHeaders.QOS, 1)
                    .build();

            mqttOutboundChannel.send(message);

            System.out.println("========== MQTT Publish ==========");
            System.out.println("Topic   : " + topic);
            System.out.println("Payload : " + payload);
            System.out.println("==================================");

        } catch (JsonProcessingException e) {
            throw new RuntimeException("MQTT 메시지 발행 실패", e);
        }
    }
}