package com.blockai.roady.auth.service;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Objects;

@Service
public class RefreshTokenService {

    private static final String KEY_PREFIX = "auth:refresh:";

    private final StringRedisTemplate redisTemplate;

    public RefreshTokenService(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public void save(Long userId, String refreshToken, Duration ttl) {
        redisTemplate.opsForValue().set(key(userId), refreshToken, ttl);
    }

    public boolean matches(Long userId, String refreshToken) {
        String savedToken = redisTemplate.opsForValue().get(key(userId));
        return Objects.equals(savedToken, refreshToken);
    }

    public void delete(Long userId) {
        redisTemplate.delete(key(userId));
    }

    private String key(Long userId) {
        return KEY_PREFIX + userId;
    }
}
