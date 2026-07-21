package com.blockai.roadbuddy.user.service;

import com.blockai.roadbuddy.user.domain.UserAccount;
import com.blockai.roadbuddy.user.domain.UserRole;

import java.util.List;
import java.util.Optional;

public interface UserAccountService {

    UserAccount create(String username, String rawPassword, String name, UserRole role);

    Optional<UserAccount> findById(String id);

    Optional<UserAccount> findByUsername(String username);

    List<UserAccount> findAll();

    UserAccount updateRole(String id, UserRole role);

    UserAccount updateActive(String id, boolean active);
}
