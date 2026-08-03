package com.blockai.roady.config;

import com.blockai.roady.security.CorsProperties;
import com.blockai.roady.robot.websocket.RobotWebSocketHandshakeInterceptor;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    private final CorsProperties corsProperties;
    private final RobotWebSocketHandshakeInterceptor robotWebSocketHandshakeInterceptor;

    public WebSocketConfig(
            CorsProperties corsProperties,
            RobotWebSocketHandshakeInterceptor robotWebSocketHandshakeInterceptor
    ) {
        this.corsProperties = corsProperties;
        this.robotWebSocketHandshakeInterceptor = robotWebSocketHandshakeInterceptor;
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.enableSimpleBroker("/topic");
        registry.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws")
                .addInterceptors(robotWebSocketHandshakeInterceptor)
                .setAllowedOrigins(corsProperties.allowedOrigins().toArray(String[]::new));
    }
}
