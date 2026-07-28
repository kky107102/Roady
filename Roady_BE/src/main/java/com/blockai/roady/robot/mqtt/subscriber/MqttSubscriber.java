package com.blockai.roady.robot.mqtt.subscriber;

import com.blockai.roady.robot.dto.CreateRobotStatusLogRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.integration.annotation.ServiceActivator;
import org.springframework.integration.mqtt.support.MqttHeaders;
import org.springframework.messaging.Message;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class MqttSubscriber {

    private final ObjectMapper objectMapper;
    @ServiceActivator(inputChannel = "mqttInputChannel")
    public CreateRobotStatusLogRequest receive(Message<String> message) {

        try {

            String topic = message.getHeaders().get(
                    MqttHeaders.RECEIVED_TOPIC,
                    String.class
            );

            String payload = message.getPayload();
            // JSON -> DTO
            CreateRobotStatusLogRequest robotStatusLogRequest =
                    objectMapper.readValue(
                            payload,
                            CreateRobotStatusLogRequest.class
                    );

            System.out.println("========== MQTT ==========");
            System.out.println("Topic   : " + topic);
            System.out.println("Payload : " + payload);

            return robotStatusLogRequest;

        } catch (Exception e) {

            System.out.println("MQTT Parsing Error");

            e.printStackTrace();

        }

        return null;
    }

}
