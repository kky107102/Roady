package com.blockai.roady.robot.websocket;

import org.springframework.stereotype.Component;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class RobotWebSocketSessionRegistry {

    private final ConcurrentHashMap<String, Long> sessionRobotIds = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<Long, Set<String>> robotSessions = new ConcurrentHashMap<>();

    public boolean register(String sessionId, Long robotId) {
        if (sessionId == null || robotId == null) {
            return false;
        }

        Long previousRobotId = sessionRobotIds.get(sessionId);
        if (previousRobotId != null && !previousRobotId.equals(robotId)) {
            unregister(sessionId);
        }

        sessionRobotIds.put(sessionId, robotId);
        Set<String> sessions = robotSessions.computeIfAbsent(robotId, ignored -> ConcurrentHashMap.newKeySet());
        boolean wasDisconnected = sessions.isEmpty();
        sessions.add(sessionId);
        return wasDisconnected;
    }

    public DisconnectResult unregister(String sessionId) {
        Long robotId = sessionRobotIds.remove(sessionId);
        if (robotId == null) {
            return DisconnectResult.notRobotSession();
        }

        Set<String> sessions = robotSessions.get(robotId);
        if (sessions == null) {
            return new DisconnectResult(robotId, true);
        }

        sessions.remove(sessionId);
        boolean disconnected = sessions.isEmpty();
        if (disconnected) {
            robotSessions.remove(robotId, sessions);
        }
        return new DisconnectResult(robotId, disconnected);
    }

    public record DisconnectResult(Long robotId, boolean disconnected) {
        private static DisconnectResult notRobotSession() {
            return new DisconnectResult(null, false);
        }
    }
}
