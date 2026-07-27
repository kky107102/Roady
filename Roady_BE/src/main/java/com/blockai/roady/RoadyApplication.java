package com.blockai.roady;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@EnableScheduling
@SpringBootApplication
public class RoadyApplication {

    public static void main(String[] args) {
        SpringApplication.run(RoadyApplication.class, args);
    }

}
