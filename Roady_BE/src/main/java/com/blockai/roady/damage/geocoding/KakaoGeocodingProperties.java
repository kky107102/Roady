package com.blockai.roady.damage.geocoding;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

@ConfigurationProperties(prefix = "roady.geocoding.kakao")
public class KakaoGeocodingProperties {

    private boolean enabled;
    private String restApiKey;
    private String coord2AddressUrl = "https://dapi.kakao.com/v2/local/geo/coord2address.json";
    private String coord2RegionCodeUrl = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json";
    private Duration requestTimeout = Duration.ofSeconds(3);

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public String getRestApiKey() {
        return restApiKey;
    }

    public void setRestApiKey(String restApiKey) {
        this.restApiKey = restApiKey;
    }

    public String getCoord2AddressUrl() {
        return coord2AddressUrl;
    }

    public void setCoord2AddressUrl(String coord2AddressUrl) {
        this.coord2AddressUrl = coord2AddressUrl;
    }

    public String getCoord2RegionCodeUrl() {
        return coord2RegionCodeUrl;
    }

    public void setCoord2RegionCodeUrl(String coord2RegionCodeUrl) {
        this.coord2RegionCodeUrl = coord2RegionCodeUrl;
    }

    public Duration getRequestTimeout() {
        return requestTimeout;
    }

    public void setRequestTimeout(Duration requestTimeout) {
        this.requestTimeout = requestTimeout;
    }
}
