package com.blockai.roady.robot.redis;

import com.blockai.roady.robot.config.RobotLocationProperties;
import com.blockai.roady.robot.dto.RobotLocationState;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.Optional;

@Component
public class RobotLocationCache {

    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    private final RobotLocationProperties properties;

    public RobotLocationCache(
            StringRedisTemplate redisTemplate,
            ObjectMapper objectMapper,
            RobotLocationProperties properties
    ) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
        this.properties = properties;
    }

    public void saveLatest(RobotLocationState state) {
        String payload = serialize(state);
        Duration ttl = properties.getTtl();
        if (ttl == null || ttl.isZero() || ttl.isNegative()) {
            redisTemplate.opsForValue().set(properties.redisKey(state.robotId()), payload);
            return;
        }
        redisTemplate.opsForValue().set(properties.redisKey(state.robotId()), payload, ttl);
    }

    public Optional<RobotLocationState> findLatest(Long robotId) {
        String payload = redisTemplate.opsForValue().get(properties.redisKey(robotId));
        if (payload == null) {
            return Optional.empty();
        }
        return Optional.of(deserialize(payload));
    }

    private String serialize(RobotLocationState state) {
        try {
            return objectMapper.writeValueAsString(state);
        } catch (JsonProcessingException ex) {
            throw new IllegalArgumentException("Failed to serialize robot location state.", ex);
        }
    }

    private RobotLocationState deserialize(String payload) {
        try {
            return objectMapper.readValue(payload, RobotLocationState.class);
        } catch (JsonProcessingException ex) {
            throw new IllegalArgumentException("Failed to deserialize robot location state.", ex);
        }
    }
}
