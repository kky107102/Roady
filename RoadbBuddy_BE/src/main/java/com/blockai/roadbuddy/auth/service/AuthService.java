package com.blockai.roadbuddy.auth.service;

import com.blockai.roadbuddy.auth.dto.TokenResponse;
import com.blockai.roadbuddy.security.AuthenticatedUser;
import com.blockai.roadbuddy.security.JwtTokenProvider;
import com.blockai.roadbuddy.security.TokenType;
import com.blockai.roadbuddy.user.domain.UserAccount;
import com.blockai.roadbuddy.user.domain.UserRole;
import com.blockai.roadbuddy.user.service.UserAccountService;
import io.jsonwebtoken.Claims;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final AuthenticationManager authenticationManager;
    private final JwtTokenProvider jwtTokenProvider;
    private final RefreshTokenService refreshTokenService;
    private final UserAccountService userAccountService;

    public AuthService(
            AuthenticationManager authenticationManager,
            JwtTokenProvider jwtTokenProvider,
            RefreshTokenService refreshTokenService,
            UserAccountService userAccountService
    ) {
        this.authenticationManager = authenticationManager;
        this.jwtTokenProvider = jwtTokenProvider;
        this.refreshTokenService = refreshTokenService;
        this.userAccountService = userAccountService;
    }

    public TokenResponse login(String username, String password) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(username, password)
        );

        UserAccount user = userAccountService.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));

        String accessToken = jwtTokenProvider.createAccessToken(user);
        String refreshToken = jwtTokenProvider.createRefreshToken(user);
        refreshTokenService.save(user.id(), refreshToken, jwtTokenProvider.refreshTokenValidity());

        return TokenResponse.bearer(
                accessToken,
                refreshToken,
                jwtTokenProvider.accessTokenValidity().toSeconds()
        );
    }

    public UserAccount signup(String username, String rawPassword, String email, String name) {
        return userAccountService.create(username, rawPassword, email, name, UserRole.VIEWER);
    }

    public TokenResponse refresh(String refreshToken) {
        jwtTokenProvider.validateTokenType(refreshToken, TokenType.REFRESH);
        Claims claims = jwtTokenProvider.parseClaims(refreshToken);
        Long userId = Long.valueOf(claims.getSubject());

        if (!refreshTokenService.matches(userId, refreshToken)) {
            throw new IllegalArgumentException("Refresh Token이 유효하지 않습니다.");
        }

        UserAccount user = userAccountService.findById(userId)
                .filter(UserAccount::active)
                .orElseThrow(() -> new IllegalArgumentException("활성 사용자를 찾을 수 없습니다."));

        String accessToken = jwtTokenProvider.createAccessToken(user);
        return TokenResponse.bearer(
                accessToken,
                refreshToken,
                jwtTokenProvider.accessTokenValidity().toSeconds()
        );
    }

    public void logout(String refreshToken) {
        jwtTokenProvider.validateTokenType(refreshToken, TokenType.REFRESH);
        AuthenticatedUser user = jwtTokenProvider.getAuthenticatedUser(refreshToken);
        refreshTokenService.delete(user.id());
    }
}
