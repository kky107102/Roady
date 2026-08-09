package com.blockai.roady.robot.mqtt.subscriber;

import com.blockai.roady.robot.mqtt.RobotMqttTopics;
import com.blockai.roady.robot.service.RobotLocationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.integration.annotation.ServiceActivator;
import org.springframework.integration.mqtt.support.MqttHeaders;
import org.springframework.messaging.Message;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class MqttSubscriber {

    private final RobotLocationService robotLocationService;

    @ServiceActivator(inputChannel = "mqttInputChannel")
    public void receive(Message<String> message) {
        String topic = message.getHeaders().get(MqttHeaders.RECEIVED_TOPIC, String.class);
        Long robotId = RobotMqttTopics.robotIdFromTelemetryTopic(topic);

        robotLocationService.saveLatest(robotId, message.getPayload());
        log.debug("Processed robot telemetry. robotId={}", robotId);
    }
}
