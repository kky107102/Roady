package com.blockai.roady.damage.queue;

import com.blockai.roady.damage.config.AiImageAnalysisProperties;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

@Component
public class DamageAnalysisQueue {

    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    private final AiImageAnalysisProperties properties;

    public DamageAnalysisQueue(
            StringRedisTemplate redisTemplate,
            ObjectMapper objectMapper,
            AiImageAnalysisProperties properties
    ) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
        this.properties = properties;
    }

    public void enqueue(DamageAnalysisQueueMessage message) {
        redisTemplate.opsForList().rightPush(properties.getQueueKey(), serialize(message));
    }

    public DamageAnalysisQueueMessage poll() {
        String payload = redisTemplate.opsForList().leftPop(properties.getQueueKey());
        if (payload == null) {
            return null;
        }
        return deserialize(payload);
    }

    public void deadLetter(DamageAnalysisQueueMessage message) {
        redisTemplate.opsForList().rightPush(properties.getDeadLetterQueueKey(), serialize(message));
    }

    private String serialize(DamageAnalysisQueueMessage message) {
        try {
            return objectMapper.writeValueAsString(message);
        } catch (JsonProcessingException ex) {
            throw new IllegalArgumentException("Failed to serialize damage analysis queue message.", ex);
        }
    }

    private DamageAnalysisQueueMessage deserialize(String payload) {
        try {
            return objectMapper.readValue(payload, DamageAnalysisQueueMessage.class);
        } catch (JsonProcessingException ex) {
            throw new IllegalArgumentException("Failed to deserialize damage analysis queue message.", ex);
        }
    }
}
