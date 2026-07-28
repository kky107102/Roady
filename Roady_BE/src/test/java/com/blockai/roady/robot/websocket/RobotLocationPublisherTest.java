package com.blockai.roady.robot.websocket;

import com.blockai.roady.robot.domain.RobotConnectionStatus;
import com.blockai.roady.robot.domain.RobotStatus;
import com.blockai.roady.robot.dto.RobotLocationState;
import org.junit.jupiter.api.Test;
import org.springframework.messaging.simp.SimpMessagingTemplate;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class RobotLocationPublisherTest {

    @Test
    void publishSendsLocationStateToAllAndRobotSpecificTopics() {
        SimpMessagingTemplate messagingTemplate = mock(SimpMessagingTemplate.class);
        RobotLocationPublisher publisher = new RobotLocationPublisher(messagingTemplate);
        RobotLocationState state = state();

        publisher.publish(state);

        verify(messagingTemplate).convertAndSend("/topic/robots/location", state);
        verify(messagingTemplate).convertAndSend("/topic/robots/10/location", state);
    }

    @Test
    void robotLocationTopicBuildsRobotSpecificTopic() {
        RobotLocationPublisher publisher = new RobotLocationPublisher(mock(SimpMessagingTemplate.class));

        assertThat(publisher.robotLocationTopic(10L)).isEqualTo("/topic/robots/10/location");
    }

    private RobotLocationState state() {
        LocalDateTime now = LocalDateTime.of(2026, 7, 28, 14, 30);
        return new RobotLocationState(
                10L,
                BigDecimal.valueOf(37.501),
                BigDecimal.valueOf(127.039),
                82,
                RobotStatus.MOVING,
                RobotConnectionStatus.CONNECTED,
                null,
                null,
                now,
                now
        );
    }
}
