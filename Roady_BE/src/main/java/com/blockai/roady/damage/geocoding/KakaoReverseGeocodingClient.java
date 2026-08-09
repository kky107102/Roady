package com.blockai.roady.damage.geocoding;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.util.CollectionUtils;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Component
public class KakaoReverseGeocodingClient {

    private static final Logger log = LoggerFactory.getLogger(KakaoReverseGeocodingClient.class);
    private static final String KAKAO_AUTHORIZATION_PREFIX = "KakaoAK ";

    private final RestClient restClient;
    private final KakaoGeocodingProperties properties;

    public KakaoReverseGeocodingClient(
            @Qualifier("kakaoGeocodingRestClient") RestClient kakaoGeocodingRestClient,
            KakaoGeocodingProperties properties
    ) {
        this.restClient = kakaoGeocodingRestClient;
        this.properties = properties;
    }

    public Optional<GeocodedAddress> reverseGeocode(BigDecimal latitude, BigDecimal longitude) {
        if (!isAvailable(latitude, longitude)) {
            return Optional.empty();
        }

        try {
            KakaoCoord2AddressResponse addressResponse = restClient.get()
                    .uri(
                            properties.getCoord2AddressUrl() + "?x={x}&y={y}&input_coord=WGS84",
                            longitude,
                            latitude
                    )
                    .header("Authorization", KAKAO_AUTHORIZATION_PREFIX + properties.getRestApiKey())
                    .retrieve()
                    .body(KakaoCoord2AddressResponse.class);
            KakaoCoord2RegionCodeResponse regionCodeResponse = restClient.get()
                    .uri(
                            properties.getCoord2RegionCodeUrl() + "?x={x}&y={y}&input_coord=WGS84",
                            longitude,
                            latitude
                    )
                    .header("Authorization", KAKAO_AUTHORIZATION_PREFIX + properties.getRestApiKey())
                    .retrieve()
                    .body(KakaoCoord2RegionCodeResponse.class);

            return toGeocodedAddress(addressResponse, regionCodeResponse);
        } catch (RuntimeException ex) {
            log.warn("Failed to reverse geocode damage coordinates. latitude={}, longitude={}", latitude, longitude, ex);
            return Optional.empty();
        }
    }

    private boolean isAvailable(BigDecimal latitude, BigDecimal longitude) {
        return properties.isEnabled()
                && StringUtils.hasText(properties.getRestApiKey())
                && StringUtils.hasText(properties.getCoord2AddressUrl())
                && StringUtils.hasText(properties.getCoord2RegionCodeUrl())
                && latitude != null
                && longitude != null;
    }

    private Optional<GeocodedAddress> toGeocodedAddress(
            KakaoCoord2AddressResponse addressResponse,
            KakaoCoord2RegionCodeResponse regionCodeResponse
    ) {
        KakaoAddressDocument document = firstAddressDocument(addressResponse).orElse(null);
        KakaoAddress address = document == null ? null : document.address();
        KakaoRoadAddress roadAddress = document == null ? null : document.roadAddress();
        KakaoRegionSource regionSource = roadAddress != null ? roadAddress : address;
        String regionCode = toSigunguCode(regionCodeResponse);

        String addressName = address == null ? null : address.addressName();
        String roadAddressName = roadAddress == null ? null : roadAddress.addressName();

        if (!StringUtils.hasText(addressName)
                && !StringUtils.hasText(roadAddressName)
                && !StringUtils.hasText(regionCode)) {
            return Optional.empty();
        }

        return Optional.of(new GeocodedAddress(
                addressName,
                roadAddressName,
                regionCode,
                regionSource == null ? null : regionSource.region1DepthName(),
                regionSource == null ? null : regionSource.region2DepthName(),
                regionSource == null ? null : regionSource.region3DepthName(),
                LocalDateTime.now()
        ));
    }

    private Optional<KakaoAddressDocument> firstAddressDocument(KakaoCoord2AddressResponse response) {
        if (response == null || CollectionUtils.isEmpty(response.documents())) {
            return Optional.empty();
        }
        return Optional.of(response.documents().getFirst());
    }

    private String toSigunguCode(KakaoCoord2RegionCodeResponse response) {
        if (response == null || CollectionUtils.isEmpty(response.documents())) {
            return null;
        }

        return response.documents().stream()
                .filter(document -> "H".equals(document.regionType()))
                .findFirst()
                .or(() -> response.documents().stream()
                        .filter(document -> "B".equals(document.regionType()))
                        .findFirst())
                .map(KakaoRegionCodeDocument::code)
                .filter(StringUtils::hasText)
                .map(code -> code.length() < 5 ? code : code.substring(0, 5))
                .orElse(null);
    }

    private interface KakaoRegionSource {

        String region1DepthName();

        String region2DepthName();

        String region3DepthName();
    }

    private record KakaoCoord2AddressResponse(
            List<KakaoAddressDocument> documents
    ) {
    }

    private record KakaoCoord2RegionCodeResponse(
            List<KakaoRegionCodeDocument> documents
    ) {
    }

    private record KakaoRegionCodeDocument(
            @JsonProperty("region_type") String regionType,
            String code
    ) {
    }

    private record KakaoAddressDocument(
            KakaoAddress address,
            @JsonProperty("road_address") KakaoRoadAddress roadAddress
    ) {
    }

    private record KakaoAddress(
            @JsonProperty("address_name") String addressName,
            @JsonProperty("region_1depth_name") String region1DepthName,
            @JsonProperty("region_2depth_name") String region2DepthName,
            @JsonProperty("region_3depth_name") String region3DepthName
    ) implements KakaoRegionSource {
    }

    private record KakaoRoadAddress(
            @JsonProperty("address_name") String addressName,
            @JsonProperty("region_1depth_name") String region1DepthName,
            @JsonProperty("region_2depth_name") String region2DepthName,
            @JsonProperty("region_3depth_name") String region3DepthName
    ) implements KakaoRegionSource {
    }
}
