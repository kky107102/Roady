package com.blockai.roady.robot.websocket;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class RobotWebSocketSessionRegistryTest {

    private final RobotWebSocketSessionRegistry registry = new RobotWebSocketSessionRegistry();

    @Test
    void registerReturnsTrueOnlyWhenRobotWasDisconnected() {
        assertThat(registry.register("session-1", 1L)).isTrue();
        assertThat(registry.register("session-2", 1L)).isFalse();
    }

    @Test
    void unregisterDisconnectsOnlyAfterLastRobotSessionIsRemoved() {
        registry.register("session-1", 1L);
        registry.register("session-2", 1L);

        var first = registry.unregister("session-1");
        var second = registry.unregister("session-2");

        assertThat(first.robotId()).isEqualTo(1L);
        assertThat(first.disconnected()).isFalse();
        assertThat(second.robotId()).isEqualTo(1L);
        assertThat(second.disconnected()).isTrue();
    }

    @Test
    void unregisterIgnoresNonRobotSession() {
        var result = registry.unregister("frontend-session");

        assertThat(result.robotId()).isNull();
        assertThat(result.disconnected()).isFalse();
    }
}
