package com.blockai.roadbuddy.security;

import com.blockai.roadbuddy.user.domain.UserAccount;
import com.blockai.roadbuddy.user.domain.UserRole;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;

@Component
public class JwtTokenProvider {

    private static final String CLAIM_USERNAME = "username";
    private static final String CLAIM_ROLE = "role";
    private static final String CLAIM_TOKEN_TYPE = "tokenType";

    private final JwtProperties properties;
    private final SecretKey secretKey;

    public JwtTokenProvider(JwtProperties properties) {
        this.properties = properties;
        this.secretKey = Keys.hmacShaKeyFor(properties.secret().getBytes(StandardCharsets.UTF_8));
    }

    public String createAccessToken(UserAccount user) {
        return createToken(user, TokenType.ACCESS, accessTokenValidity());
    }

    public String createRefreshToken(UserAccount user) {
        return createToken(user, TokenType.REFRESH, refreshTokenValidity());
    }

    public Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public AuthenticatedUser getAuthenticatedUser(String token) {
        Claims claims = parseClaims(token);
        return new AuthenticatedUser(
                claims.getSubject(),
                claims.get(CLAIM_USERNAME, String.class),
                UserRole.valueOf(claims.get(CLAIM_ROLE, String.class))
        );
    }

    public boolean isTokenType(String token, TokenType expectedTokenType) {
        Claims claims = parseClaims(token);
        String tokenType = claims.get(CLAIM_TOKEN_TYPE, String.class);
        return expectedTokenType.name().equals(tokenType);
    }

    public Duration accessTokenValidity() {
        return Duration.ofMinutes(properties.accessTokenValidityMinutes());
    }

    public Duration refreshTokenValidity() {
        return Duration.ofDays(properties.refreshTokenValidityDays());
    }

    public void validateTokenType(String token, TokenType expectedTokenType) {
        if (!isTokenType(token, expectedTokenType)) {
            throw new JwtException("토큰 유형이 올바르지 않습니다.");
        }
    }

    private String createToken(UserAccount user, TokenType tokenType, Duration validity) {
        Instant now = Instant.now();
        Instant expiresAt = now.plus(validity);

        return Jwts.builder()
                .subject(user.id())
                .claim(CLAIM_USERNAME, user.username())
                .claim(CLAIM_ROLE, user.role().name())
                .claim(CLAIM_TOKEN_TYPE, tokenType.name())
                .issuedAt(Date.from(now))
                .expiration(Date.from(expiresAt))
                .signWith(secretKey, Jwts.SIG.HS256)
                .compact();
    }
}
