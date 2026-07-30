package com.blockai.roady.damage.geocoding;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class KakaoReverseGeocodingClientTest {

    @Test
    void reverseGeocodeMapsKakaoAddressResponse() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        KakaoReverseGeocodingClient client = new KakaoReverseGeocodingClient(
                builder.build(),
                properties(true, "test-key")
        );
        server.expect(requestTo(
                        "https://dapi.kakao.com/v2/local/geo/coord2address.json"
                                + "?x=127.1234567&y=37.1234567&input_coord=WGS84"
                ))
                .andExpect(header("Authorization", "KakaoAK test-key"))
                .andRespond(withSuccess(
                        """
                        {
                          "documents": [
                            {
                              "address": {
                                "address_name": "Gyeonggi Anseong Juksan 343-1",
                                "region_1depth_name": "Gyeonggi",
                                "region_2depth_name": "Anseong",
                                "region_3depth_name": "Juksan"
                              },
                              "road_address": {
                                "address_name": "Gyeonggi Anseong Juksanchogyogil 69-4",
                                "region_1depth_name": "Gyeonggi",
                                "region_2depth_name": "Anseong",
                                "region_3depth_name": "Juksan"
                              }
                            }
                          ]
                        }
                        """,
                        MediaType.APPLICATION_JSON
                ));

        var result = client.reverseGeocode(
                BigDecimal.valueOf(37.1234567),
                BigDecimal.valueOf(127.1234567)
        );

        assertThat(result).isPresent();
        assertThat(result.get().addressName()).isEqualTo("Gyeonggi Anseong Juksan 343-1");
        assertThat(result.get().roadAddressName()).isEqualTo("Gyeonggi Anseong Juksanchogyogil 69-4");
        assertThat(result.get().region1DepthName()).isEqualTo("Gyeonggi");
        assertThat(result.get().region2DepthName()).isEqualTo("Anseong");
        assertThat(result.get().region3DepthName()).isEqualTo("Juksan");
        assertThat(result.get().geocodedAt()).isNotNull();
        server.verify();
    }

    @Test
    void reverseGeocodeSkipsRequestWhenDisabled() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        KakaoReverseGeocodingClient client = new KakaoReverseGeocodingClient(
                builder.build(),
                properties(false, "test-key")
        );

        var result = client.reverseGeocode(
                BigDecimal.valueOf(37.1234567),
                BigDecimal.valueOf(127.1234567)
        );

        assertThat(result).isEmpty();
        server.verify();
    }

    private KakaoGeocodingProperties properties(boolean enabled, String restApiKey) {
        KakaoGeocodingProperties properties = new KakaoGeocodingProperties();
        properties.setEnabled(enabled);
        properties.setRestApiKey(restApiKey);
        return properties;
    }
}
