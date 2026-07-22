package com.blockai.roadbuddy.user.service;

import com.blockai.roadbuddy.user.domain.UserRole;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

@Component
@Profile("!inmemory")
public class UserDataInitializer implements ApplicationRunner {

    private final UserAccountService userAccountService;

    public UserDataInitializer(UserAccountService userAccountService) {
        this.userAccountService = userAccountService;
    }

    @Override
    public void run(ApplicationArguments args) {
        seedUser("admin", "admin1234", "admin@roadbuddy.local", "관리자", UserRole.ADMIN);
        seedUser("inspector", "inspector1234", "inspector@roadbuddy.local", "점검 담당자", UserRole.INSPECTOR);
        seedUser("repairer", "repairer1234", "repairer@roadbuddy.local", "보수 담당자", UserRole.REPAIRER);
        seedUser("viewer", "viewer1234", "viewer@roadbuddy.local", "조회 사용자", UserRole.VIEWER);
    }

    private void seedUser(String username, String password, String email, String name, UserRole role) {
        if (userAccountService.findByUsername(username).isPresent()) {
            return;
        }
        userAccountService.create(username, password, email, name, role);
    }
}
