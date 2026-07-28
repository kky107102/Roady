package com.blockai.roady.robot.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(RobotLocationProperties.class)
public class RobotLocationConfig {
}
