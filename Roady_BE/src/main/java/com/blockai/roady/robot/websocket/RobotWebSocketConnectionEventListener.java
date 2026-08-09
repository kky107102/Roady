package com.blockai.roady.robot.websocket;

import com.blockai.roady.robot.domain.RobotConnectionStatus;
import com.blockai.roady.robot.service.RobotConnectionStatusService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.event.EventListener;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.messaging.SessionConnectEvent;
import org.springframework.web.socket.messaging.SessionDisconnectEvent;

import java.util.Map;
import java.util.Optional;

@Component
public class RobotWebSocketConnectionEventListener {

    private static final Logger log = LoggerFactory.getLogger(RobotWebSocketConnectionEventListener.class);

    private final RobotWebSocketSessionRegistry sessionRegistry;
    private final RobotConnectionStatusService robotConnectionStatusService;

    public RobotWebSocketConnectionEventListener(
            RobotWebSocketSessionRegistry sessionRegistry,
            RobotConnectionStatusService robotConnectionStatusService
    ) {
        this.sessionRegistry = sessionRegistry;
        this.robotConnectionStatusService = robotConnectionStatusService;
    }

    @EventListener
    public void handleSessionConnect(SessionConnectEvent event) {
        StompHeaderAccessor accessor = StompHeaderAccessor.wrap(event.getMessage());
        String sessionId = accessor.getSessionId();
        Optional<Long> robotId = resolveRobotId(accessor);
        if (sessionId == null || robotId.isEmpty()) {
            return;
        }

        boolean wasDisconnected = sessionRegistry.register(sessionId, robotId.get());
        if (wasDisconnected) {
            updateConnectionStatus(robotId.get(), RobotConnectionStatus.CONNECTED);
        }
    }

    @EventListener
    public void handleSessionDisconnect(SessionDisconnectEvent event) {
        StompHeaderAccessor accessor = StompHeaderAccessor.wrap(event.getMessage());
        RobotWebSocketSessionRegistry.DisconnectResult result = sessionRegistry.unregister(accessor.getSessionId());
        if (result.robotId() != null && result.disconnected()) {
            updateConnectionStatus(result.robotId(), RobotConnectionStatus.DISCONNECTED);
        }
    }

    private Optional<Long> resolveRobotId(StompHeaderAccessor accessor) {
        String robotId = accessor.getFirstNativeHeader(RobotWebSocketHandshakeInterceptor.ROBOT_ID_ATTRIBUTE);
        if (robotId == null || robotId.isBlank()) {
            Map<String, Object> sessionAttributes = accessor.getSessionAttributes();
            Object attribute = sessionAttributes == null
                    ? null
                    : sessionAttributes.get(RobotWebSocketHandshakeInterceptor.ROBOT_ID_ATTRIBUTE);
            robotId = attribute == null ? null : String.valueOf(attribute);
        }

        if (robotId == null || robotId.isBlank()) {
            return Optional.empty();
        }

        try {
            Long parsed = Long.valueOf(robotId);
            return parsed > 0 ? Optional.of(parsed) : Optional.empty();
        } catch (NumberFormatException ex) {
            log.warn("Ignoring robot WebSocket session with invalid robotId header: {}", robotId);
            return Optional.empty();
        }
    }

    private void updateConnectionStatus(Long robotId, RobotConnectionStatus connectionStatus) {
        try {
            robotConnectionStatusService.updateConnectionStatus(robotId, connectionStatus);
        } catch (RuntimeException ex) {
            log.warn("Failed to update robot {} WebSocket connection status to {}.", robotId, connectionStatus, ex);
        }
    }
}
