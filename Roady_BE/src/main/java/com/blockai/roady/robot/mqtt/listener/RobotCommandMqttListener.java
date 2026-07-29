package com.blockai.roady.robot.mqtt.listener;

import com.blockai.roady.robot.mqtt.event.RobotCommandCreatedEvent;
import com.blockai.roady.robot.mqtt.publisher.MqttPublisher;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Component
@RequiredArgsConstructor
@Slf4j
@ConditionalOnProperty(name = "mqtt.enabled", havingValue = "true", matchIfMissing = true)
public class RobotCommandMqttListener {

    private final MqttPublisher mqttPublisher;

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void publishCommand(RobotCommandCreatedEvent event) {
        try {
            mqttPublisher.publishCommand(event.robotId(), event.message());
        } catch (RuntimeException ex) {
            log.error(
                    "Failed to publish robot command. robotId={}, commandId={}",
                    event.robotId(),
                    event.message().commandId(),
                    ex
            );
        }
    }
}
