package com.blockai.roady.robot.mqtt;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class RobotMqttTopicsTest {

    @Test
    void extractsRobotIdFromTelemetryTopic() {
        assertThat(RobotMqttTopics.robotIdFromTelemetryTopic("roady/10/telemetry")).isEqualTo(10L);
    }

    @Test
    void rejectsMalformedTelemetryTopics() {
        assertThatThrownBy(() -> RobotMqttTopics.robotIdFromTelemetryTopic("roady/robot-a/telemetry"))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> RobotMqttTopics.robotIdFromTelemetryTopic("roady/10/status"))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> RobotMqttTopics.robotIdFromTelemetryTopic("roady/0/telemetry"))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void buildsCommandTopic() {
        assertThat(RobotMqttTopics.commandTopic(10L)).isEqualTo("roady/10/command");
        assertThatThrownBy(() -> RobotMqttTopics.commandTopic(0L))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void extractsRobotIdFromCommandAckTopic() {
        assertThat(RobotMqttTopics.robotIdFromCommandAckTopic("roady/10/command/ack")).isEqualTo(10L);
        assertThatThrownBy(() -> RobotMqttTopics.robotIdFromCommandAckTopic("roady/10/ack"))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
