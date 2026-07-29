package com.blockai.roady.robot.mqtt.subscriber;

import com.blockai.roady.robot.mqtt.RobotMqttTopics;
import com.blockai.roady.robot.service.RobotCommandAckService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.integration.annotation.ServiceActivator;
import org.springframework.integration.mqtt.support.MqttHeaders;
import org.springframework.messaging.Message;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class MqttCommandAckSubscriber {

    private final RobotCommandAckService robotCommandAckService;

    @ServiceActivator(inputChannel = "mqttCommandAckInputChannel")
    public void receive(Message<String> message) {
        String topic = message.getHeaders().get(MqttHeaders.RECEIVED_TOPIC, String.class);
        Long robotId = RobotMqttTopics.robotIdFromCommandAckTopic(topic);

        robotCommandAckService.handle(robotId, message.getPayload());
        log.debug("Processed robot command ACK. robotId={}", robotId);
    }
}
