package com.blockai.roady.user.service;

import com.blockai.roady.user.domain.UserAccount;
import com.blockai.roady.user.domain.UserRole;
import com.blockai.roady.user.mapper.UserAccountMapper;
import org.springframework.context.annotation.Profile;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.Optional;

@Service
@Profile("!inmemory")
public class DbUserAccountService implements UserAccountService {

    private final UserAccountMapper userAccountMapper;
    private final PasswordEncoder passwordEncoder;

    public DbUserAccountService(UserAccountMapper userAccountMapper, PasswordEncoder passwordEncoder) {
        this.userAccountMapper = userAccountMapper;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public UserAccount create(String username, String rawPassword, String email, String name, UserRole role) {
        validateDuplicate(username, email);

        try {
            userAccountMapper.insert(
                    username,
                    passwordEncoder.encode(rawPassword),
                    email,
                    name,
                    role
            );
        } catch (DuplicateKeyException ex) {
            throw new IllegalArgumentException("이미 사용 중인 아이디 또는 이메일입니다.");
        }

        return findByUsername(username)
                .orElseThrow(() -> new IllegalStateException("생성된 사용자를 찾을 수 없습니다."));
    }

    @Override
    public Optional<UserAccount> findById(Long id) {
        return Optional.ofNullable(userAccountMapper.findById(id));
    }

    @Override
    public Optional<UserAccount> findByUsername(String username) {
        return Optional.ofNullable(userAccountMapper.findByUsername(username));
    }

    @Override
    public List<UserAccount> findAll() {
        return userAccountMapper.findAll();
    }

    @Override
    public List<UserAccount> findAll(UserRole role, Boolean active) {
        return userAccountMapper.findAllByFilters(role, active);
    }

    @Override
    public UserAccount updateRole(Long id, UserRole role) {
        int updatedRows = userAccountMapper.updateRole(id, role);
        if (updatedRows == 0) {
            throw new IllegalArgumentException("사용자를 찾을 수 없습니다.");
        }
        return findById(id).orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));
    }

    @Override
    public UserAccount updateActive(Long id, boolean active) {
        int updatedRows = userAccountMapper.updateActive(id, active);
        if (updatedRows == 0) {
            throw new IllegalArgumentException("사용자를 찾을 수 없습니다.");
        }
        return findById(id).orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));
    }

    @Override
    public UserAccount updateAssignedRegion(Long id, String assignedRegionCode) {
        String normalizedRegionCode = normalizeRegionCode(assignedRegionCode);

        int updatedRows = userAccountMapper.updateAssignedRegion(id, normalizedRegionCode);
        if (updatedRows == 0) {
            throw new IllegalArgumentException("User not found.");
        }
        return findById(id).orElseThrow(() -> new IllegalArgumentException("User not found."));
    }

    private String normalizeRegionCode(String regionCode) {
        if (!StringUtils.hasText(regionCode)) {
            return null;
        }
        return regionCode.trim();
    }

    private void validateDuplicate(String username, String email) {
        if (userAccountMapper.existsByUsername(username)) {
            throw new IllegalArgumentException("이미 사용 중인 아이디입니다.");
        }
        if (userAccountMapper.existsByEmail(email)) {
            throw new IllegalArgumentException("이미 사용 중인 이메일입니다.");
        }
    }
}
