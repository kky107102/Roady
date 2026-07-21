package com.blockai.roadbuddy.user.service;

import com.blockai.roadbuddy.user.domain.UserAccount;
import com.blockai.roadbuddy.user.domain.UserRole;
import org.springframework.context.annotation.Primary;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

@Primary
@Service
public class InMemoryUserAccountService implements UserAccountService {

    private final PasswordEncoder passwordEncoder;
    private final Map<String, UserAccount> usersById = new ConcurrentHashMap<>();
    private final Map<String, String> userIdsByUsername = new ConcurrentHashMap<>();

    public InMemoryUserAccountService(PasswordEncoder passwordEncoder) {
        this.passwordEncoder = passwordEncoder;
        seedUser("admin", "admin1234", "관리자", UserRole.ADMIN);
        seedUser("inspector", "inspector1234", "점검 담당자", UserRole.INSPECTOR);
        seedUser("repairer", "repairer1234", "보수 담당자", UserRole.REPAIRER);
        seedUser("viewer", "viewer1234", "조회 사용자", UserRole.VIEWER);
    }

    @Override
    public UserAccount create(String username, String rawPassword, String name, UserRole role) {
        if (userIdsByUsername.containsKey(username)) {
            throw new IllegalArgumentException("이미 사용 중인 아이디입니다.");
        }

        UserAccount user = UserAccount.create(
                username,
                passwordEncoder.encode(rawPassword),
                name,
                role
        );
        usersById.put(user.id(), user);
        userIdsByUsername.put(user.username(), user.id());
        return user;
    }

    @Override
    public Optional<UserAccount> findById(String id) {
        return Optional.ofNullable(usersById.get(id));
    }

    @Override
    public Optional<UserAccount> findByUsername(String username) {
        return Optional.ofNullable(userIdsByUsername.get(username))
                .map(usersById::get);
    }

    @Override
    public List<UserAccount> findAll() {
        return usersById.values().stream()
                .sorted(Comparator.comparing(UserAccount::createdAt))
                .toList();
    }

    @Override
    public UserAccount updateRole(String id, UserRole role) {
        return usersById.compute(id, (ignored, user) -> {
            if (user == null) {
                throw new IllegalArgumentException("사용자를 찾을 수 없습니다.");
            }
            return user.withRole(role);
        });
    }

    @Override
    public UserAccount updateActive(String id, boolean active) {
        return usersById.compute(id, (ignored, user) -> {
            if (user == null) {
                throw new IllegalArgumentException("사용자를 찾을 수 없습니다.");
            }
            return user.withActive(active);
        });
    }

    private void seedUser(String username, String password, String name, UserRole role) {
        create(username, password, name, role);
    }
}
