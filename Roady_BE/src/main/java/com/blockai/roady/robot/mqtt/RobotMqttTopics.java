package com.blockai.roady.robot.mqtt;

public final class RobotMqttTopics {

    public static final String TELEMETRY_FILTER = "roady/+/telemetry";

    private RobotMqttTopics() {
    }

    public static Long robotIdFromTelemetryTopic(String topic) {
        if (topic == null) {
            throw new IllegalArgumentException("MQTT topic is required.");
        }

        String[] segments = topic.split("/", -1);
        if (segments.length != 3
                || !"roady".equals(segments[0])
                || !"telemetry".equals(segments[2])) {
            throw new IllegalArgumentException("Invalid robot telemetry topic.");
        }

        try {
            long robotId = Long.parseLong(segments[1]);
            if (robotId <= 0) {
                throw new IllegalArgumentException("Robot id must be positive.");
            }
            return robotId;
        } catch (NumberFormatException ex) {
            throw new IllegalArgumentException("Robot id must be a number.", ex);
        }
    }
}
