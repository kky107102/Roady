package com.blockai.roady.robot.websocket;

import com.blockai.roady.robot.dto.RobotLocationState;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

@Component
public class RobotLocationPublisher {

    public static final String ALL_ROBOT_LOCATION_TOPIC = "/topic/robots/location";
    public static final String ROBOT_LOCATION_TOPIC_PREFIX = "/topic/robots/";
    public static final String ROBOT_LOCATION_TOPIC_SUFFIX = "/location";

    private final SimpMessagingTemplate messagingTemplate;

    public RobotLocationPublisher(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    public void publish(RobotLocationState state) {
        messagingTemplate.convertAndSend(ALL_ROBOT_LOCATION_TOPIC, state);
        messagingTemplate.convertAndSend(robotLocationTopic(state.robotId()), state);
    }

    public String robotLocationTopic(Long robotId) {
        return ROBOT_LOCATION_TOPIC_PREFIX + robotId + ROBOT_LOCATION_TOPIC_SUFFIX;
    }
}
