package com.blockai.roady.security;

import com.blockai.roady.user.domain.UserAccount;
import com.blockai.roady.user.service.UserAccountService;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class RoadyUserDetailsService implements UserDetailsService {

    private final UserAccountService userAccountService;

    public RoadyUserDetailsService(UserAccountService userAccountService) {
        this.userAccountService = userAccountService;
    }

    @Override
    public UserDetails loadUserByUsername(String username) {
        UserAccount user = userAccountService.findByUsername(username)
                .orElseThrow(() -> new UsernameNotFoundException("사용자를 찾을 수 없습니다."));

        return User.withUsername(user.username())
                .password(user.password())
                .authorities("ROLE_" + user.role().name())
                .disabled(!user.active())
                .build();
    }
}
