package com.blockai.roady.damage.geocoding;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Configuration
@EnableConfigurationProperties(KakaoGeocodingProperties.class)
public class KakaoGeocodingConfig {

    @Bean
    public RestClient kakaoGeocodingRestClient(KakaoGeocodingProperties properties) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(properties.getRequestTimeout());
        requestFactory.setReadTimeout(properties.getRequestTimeout());

        return RestClient.builder()
                .requestFactory(requestFactory)
                .build();
    }
}
