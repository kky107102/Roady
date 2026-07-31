package com.blockai.roady.damage.service;

import com.blockai.roady.damage.domain.Damage;
import com.blockai.roady.damage.domain.DamageDashboardSummary;
import com.blockai.roady.damage.domain.DamageFilterCriteria;
import com.blockai.roady.damage.domain.DamageImage;
import com.blockai.roady.damage.domain.DamageMapBounds;
import com.blockai.roady.damage.domain.DamageMapMarker;
import com.blockai.roady.damage.domain.DamageSearchCriteria;
import com.blockai.roady.damage.domain.DamageSearchItem;
import com.blockai.roady.damage.domain.DamageSearchPage;
import com.blockai.roady.damage.domain.DamageStatusCount;
import com.blockai.roady.damage.domain.DamageStatus;
import com.blockai.roady.damage.domain.DamageSummary;
import com.blockai.roady.damage.geocoding.GeocodedAddress;
import com.blockai.roady.damage.geocoding.KakaoReverseGeocodingClient;
import com.blockai.roady.damage.mapper.DamageMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class DamageServiceTest {

    private static final String ADDRESS_NAME = "Gyeonggi Anseong Juksan 343-1";
    private static final String ROAD_ADDRESS_NAME = "Gyeonggi Anseong Juksanchogyogil 69-4";

    @Mock
    private DamageMapper damageMapper;

    @Mock
    private KakaoReverseGeocodingClient geocodingClient;

    @InjectMocks
    private DamageService damageService;

    @Test
    void createStoresDamageAddressWhenReverseGeocodingSucceeds() {
        LocalDateTime capturedAt = LocalDateTime.of(2026, 7, 22, 10, 30);
        LocalDateTime geocodedAt = LocalDateTime.of(2026, 7, 22, 10, 31);
        MockMultipartFile firstImage = image("first.jpg");
        MockMultipartFile secondImage = image("second.jpg");

        when(geocodingClient.reverseGeocode(
                BigDecimal.valueOf(37.1234567),
                BigDecimal.valueOf(127.1234567)
        )).thenReturn(Optional.of(new GeocodedAddress(
                ADDRESS_NAME,
                ROAD_ADDRESS_NAME,
                "41550",
                "Gyeonggi",
                "Anseong",
                "Juksan",
                geocodedAt
        )));
        doAnswer(invocation -> {
            Damage damage = invocation.getArgument(0);
            damage.setId(1L);
            return 1;
        }).when(damageMapper).insertDamage(any(Damage.class));
        when(damageMapper.findSummaryById(1L)).thenReturn(new DamageSummary(
                1L,
                10L,
                2L,
                3L,
                "tactile block damage",
                ADDRESS_NAME,
                ROAD_ADDRESS_NAME,
                "41550",
                "Gyeonggi",
                "Anseong",
                "Juksan",
                geocodedAt,
                BigDecimal.valueOf(37.1234567),
                BigDecimal.valueOf(127.1234567),
                capturedAt,
                "COLLECTED",
                2L,
                capturedAt,
                capturedAt
        ));

        DamageSummary result = damageService.create(
                10L,
                2L,
                3L,
                "tactile block damage",
                BigDecimal.valueOf(37.1234567),
                BigDecimal.valueOf(127.1234567),
                capturedAt,
                List.of(firstImage, secondImage)
        );

        ArgumentCaptor<Damage> damageCaptor = ArgumentCaptor.forClass(Damage.class);
        ArgumentCaptor<DamageImage> imageCaptor = ArgumentCaptor.forClass(DamageImage.class);
        verify(damageMapper).insertDamage(damageCaptor.capture());
        verify(damageMapper, org.mockito.Mockito.times(2)).insertImage(imageCaptor.capture());

        Damage savedDamage = damageCaptor.getValue();
        assertThat(savedDamage.getRobotId()).isEqualTo(10L);
        assertThat(savedDamage.getReportedBy()).isEqualTo(2L);
        assertThat(savedDamage.getAssignedTo()).isEqualTo(3L);
        assertThat(savedDamage.getAddressName()).isEqualTo(ADDRESS_NAME);
        assertThat(savedDamage.getRoadAddressName()).isEqualTo(ROAD_ADDRESS_NAME);
        assertThat(savedDamage.getRegionCode()).isEqualTo("41550");
        assertThat(savedDamage.getRegion1DepthName()).isEqualTo("Gyeonggi");
        assertThat(savedDamage.getRegion2DepthName()).isEqualTo("Anseong");
        assertThat(savedDamage.getRegion3DepthName()).isEqualTo("Juksan");
        assertThat(savedDamage.getGeocodedAt()).isEqualTo(geocodedAt);

        List<DamageImage> savedImages = imageCaptor.getAllValues();
        assertThat(savedImages).extracting(DamageImage::getSortOrder).containsExactly(1, 2);
        assertThat(savedImages).extracting(DamageImage::getOriginalFilename)
                .containsExactly("first.jpg", "second.jpg");
        assertThat(result.imageCount()).isEqualTo(2L);
    }

    @Test
    void createStoresDamageWithoutAddressWhenReverseGeocodingReturnsEmpty() {
        MockMultipartFile image = image("damage.jpg");
        when(geocodingClient.reverseGeocode(null, null)).thenReturn(Optional.empty());
        doAnswer(invocation -> {
            Damage damage = invocation.getArgument(0);
            damage.setId(1L);
            return 1;
        }).when(damageMapper).insertDamage(any(Damage.class));
        when(damageMapper.findSummaryById(1L)).thenReturn(new DamageSummary(
                1L,
                null,
                2L,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                "COLLECTED",
                1L,
                null,
                null
        ));

        damageService.create(null, 2L, null, null, null, null, null, List.of(image));

        ArgumentCaptor<Damage> damageCaptor = ArgumentCaptor.forClass(Damage.class);
        verify(damageMapper).insertDamage(damageCaptor.capture());
        assertThat(damageCaptor.getValue().getAddressName()).isNull();
        assertThat(damageCaptor.getValue().getRoadAddressName()).isNull();
        assertThat(damageCaptor.getValue().getGeocodedAt()).isNull();
    }

    @Test
    void createRejectsNonImageFile() {
        MockMultipartFile textFile = new MockMultipartFile(
                "images",
                "memo.txt",
                "text/plain",
                "not-image".getBytes()
        );

        assertThatThrownBy(() -> damageService.create(
                null,
                2L,
                null,
                null,
                null,
                null,
                null,
                List.of(textFile)
        )).isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Only image files can be uploaded.");

        verify(damageMapper, never()).insertDamage(any(Damage.class));
        verify(damageMapper, never()).insertImage(any(DamageImage.class));
        verify(damageMapper, never()).findSummaryById(eq(1L));
        verify(geocodingClient, never()).reverseGeocode(any(), any());
    }

    @Test
    void searchReturnsFilteredPage() {
        LocalDateTime from = LocalDateTime.of(2026, 7, 1, 0, 0);
        LocalDateTime to = LocalDateTime.of(2026, 8, 1, 0, 0);
        DamageSearchCriteria criteria = new DamageSearchCriteria(
                from,
                to,
                "AI_ANALYZED",
                10L,
                3L,
                "41550",
                "Juksan",
                1,
                20
        );
        DamageSearchItem summary = new DamageSearchItem(
                1L,
                10L,
                3L,
                "tactile block damage",
                ADDRESS_NAME,
                ROAD_ADDRESS_NAME,
                "41550",
                "Gyeonggi",
                "Anseong",
                "Juksan",
                LocalDateTime.of(2026, 7, 22, 10, 31),
                BigDecimal.valueOf(37.1234567),
                BigDecimal.valueOf(127.1234567),
                LocalDateTime.of(2026, 7, 22, 10, 30),
                "AI_ANALYZED",
                2L,
                82,
                "CRACK",
                true,
                "HIGH",
                BigDecimal.valueOf(0.91),
                LocalDateTime.of(2026, 7, 22, 10, 31)
        );

        when(damageMapper.searchSummaries(
                from,
                to,
                "AI_ANALYZED",
                10L,
                3L,
                "41550",
                null,
                "Juksan",
                20L,
                20
        )).thenReturn(List.of(summary));
        when(damageMapper.countSummaries(
                from,
                to,
                "AI_ANALYZED",
                10L,
                3L,
                "41550",
                null,
                "Juksan"
        )).thenReturn(41L);

        DamageSearchPage result = damageService.search(criteria);

        assertThat(result.content()).containsExactly(summary);
        assertThat(result.page()).isEqualTo(1);
        assertThat(result.size()).isEqualTo(20);
        assertThat(result.totalElements()).isEqualTo(41);
        assertThat(result.totalPages()).isEqualTo(3);
    }

    @Test
    void searchReturnsZeroTotalPagesForEmptyResult() {
        DamageSearchCriteria criteria = new DamageSearchCriteria(
                null,
                null,
                null,
                null,
                null,
                null,
                0,
                20
        );
        when(damageMapper.searchSummaries(null, null, null, null, null, null, null, null, 0L, 20))
                .thenReturn(List.of());
        when(damageMapper.countSummaries(null, null, null, null, null, null, null, null))
                .thenReturn(0L);

        DamageSearchPage result = damageService.search(criteria);

        assertThat(result.content()).isEmpty();
        assertThat(result.totalElements()).isZero();
        assertThat(result.totalPages()).isZero();
    }

    @Test
    void searchCriteriaRejectsInvalidPageConditions() {
        assertThatThrownBy(() -> new DamageSearchCriteria(
                null,
                null,
                null,
                null,
                null,
                null,
                -1,
                20
        )).isInstanceOf(IllegalArgumentException.class)
                .hasMessage("page must be 0 or greater.");

        assertThatThrownBy(() -> new DamageSearchCriteria(
                null,
                null,
                null,
                null,
                null,
                null,
                0,
                101
        )).isInstanceOf(IllegalArgumentException.class)
                .hasMessage("size must be between 1 and 100.");
    }

    @Test
    void searchCriteriaRejectsInvalidPeriodAndStatus() {
        LocalDateTime from = LocalDateTime.of(2026, 8, 1, 0, 0);
        LocalDateTime to = LocalDateTime.of(2026, 7, 1, 0, 0);

        assertThatThrownBy(() -> new DamageSearchCriteria(
                from,
                to,
                null,
                null,
                null,
                null,
                0,
                20
        )).isInstanceOf(IllegalArgumentException.class)
                .hasMessage("from must be earlier than to.");

        assertThatThrownBy(() -> new DamageSearchCriteria(
                null,
                null,
                "UNKNOWN",
                null,
                null,
                null,
                0,
                20
        )).isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid damage status.");
    }

    @Test
    void searchCriteriaParsesCaseNumberAndEscapesAddressKeyword() {
        DamageSearchCriteria numeric = new DamageSearchCriteria(null, null, null, null, null, "42", 0, 20);
        DamageSearchCriteria text = new DamageSearchCriteria(null, null, null, null, null, " road_% ", 0, 20);

        assertThat(numeric.caseNumber()).isEqualTo(42L);
        assertThat(numeric.addressKeyword()).isEqualTo("42");
        assertThat(text.caseNumber()).isNull();
        assertThat(text.keyword()).isEqualTo("road_%");
        assertThat(text.addressKeyword()).isEqualTo("road\\_\\%");
    }

    @Test
    void summarizeReturnsTotalsAndZeroFilledStatusCounts() {
        LocalDateTime from = LocalDateTime.of(2026, 7, 1, 0, 0);
        LocalDateTime to = LocalDateTime.of(2026, 8, 1, 0, 0);
        DamageFilterCriteria criteria = new DamageFilterCriteria(from, to, null, 10L, null);
        when(damageMapper.summarizeByStatus(from, to, null, 10L, null, null))
                .thenReturn(List.of(
                        new DamageStatusCount("COLLECTED", 3, 2),
                        new DamageStatusCount("AI_ANALYZED", 2, 1)
                ));

        DamageDashboardSummary result = damageService.summarize(criteria);

        assertThat(result.total()).isEqualTo(5);
        assertThat(result.unassigned()).isEqualTo(3);
        assertThat(result.statusCounts())
                .containsEntry("COLLECTED", 3L)
                .containsEntry("AI_ANALYZED", 2L)
                .containsEntry("REPAIR_COMPLETED", 0L)
                .hasSize(8);
    }

    @Test
    void summarizeReturnsZeroFilledResponseForEmptyResult() {
        DamageFilterCriteria criteria = new DamageFilterCriteria(null, null, null, null, null);
        when(damageMapper.summarizeByStatus(null, null, null, null, null, null))
                .thenReturn(List.of());

        DamageDashboardSummary result = damageService.summarize(criteria);

        assertThat(result.total()).isZero();
        assertThat(result.unassigned()).isZero();
        assertThat(result.statusCounts())
                .hasSize(8)
                .allSatisfy((status, count) -> assertThat(count).isZero());
    }

    @Test
    void findMapMarkersUsesCommonDamageFilters() {
        LocalDateTime from = LocalDateTime.of(2026, 7, 1, 0, 0);
        LocalDateTime to = LocalDateTime.of(2026, 8, 1, 0, 0);
        DamageFilterCriteria criteria = new DamageFilterCriteria(
                from,
                to,
                "AI_ANALYZED",
                10L,
                3L,
                "41550"
        );
        DamageMapMarker marker = new DamageMapMarker(
                1L,
                BigDecimal.valueOf(37.5665),
                BigDecimal.valueOf(126.978),
                "AI_ANALYZED"
        );
        DamageMapBounds bounds = new DamageMapBounds(
                BigDecimal.valueOf(37.45),
                BigDecimal.valueOf(37.62),
                BigDecimal.valueOf(126.80),
                BigDecimal.valueOf(127.10)
        );
        when(damageMapper.findMapMarkers(
                from,
                to,
                "AI_ANALYZED",
                10L,
                3L,
                "41550",
                bounds.south(),
                bounds.north(),
                bounds.west(),
                bounds.east()
        ))
                .thenReturn(List.of(marker));

        assertThat(damageService.findMapMarkers(criteria, bounds)).containsExactly(marker);
    }

    @Test
    void updateReviewStatusChangesAiAnalyzedDamageToRequested() {
        when(damageMapper.findSummaryById(1L)).thenReturn(damageSummary("AI_ANALYZED"));
        when(damageMapper.updateStatusIfCurrent(1L, "AI_ANALYZED", "REQUESTED"))
                .thenReturn(1);

        damageService.updateReviewStatus(1L, DamageStatus.REQUESTED);

        verify(damageMapper).updateStatusIfCurrent(1L, "AI_ANALYZED", "REQUESTED");
    }

    @Test
    void updateReviewStatusRejectsNonVerdictTarget() {
        assertThatThrownBy(
                () -> damageService.updateReviewStatus(1L, DamageStatus.REPAIR_COMPLETED)
        )
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Administrator verdict status must be REQUESTED or CANCELED.");

        verify(damageMapper, never()).findSummaryById(any());
    }

    @Test
    void updateReviewStatusRejectsDamageThatIsAlreadyReviewed() {
        when(damageMapper.findSummaryById(1L)).thenReturn(damageSummary("REQUESTED"));

        assertThatThrownBy(
                () -> damageService.updateReviewStatus(1L, DamageStatus.CANCELED)
        )
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Only AI_ANALYZED damage can receive an administrator verdict.");

        verify(damageMapper, never()).updateStatusIfCurrent(any(), any(), any());
    }

    private DamageSummary damageSummary(String status) {
        LocalDateTime timestamp = LocalDateTime.of(2026, 7, 31, 10, 0);
        return new DamageSummary(
                1L,
                10L,
                2L,
                null,
                "tactile block damage",
                ADDRESS_NAME,
                ROAD_ADDRESS_NAME,
                "41550",
                "Gyeonggi",
                "Anseong",
                "Juksan",
                timestamp,
                BigDecimal.valueOf(37.5665),
                BigDecimal.valueOf(126.978),
                timestamp,
                status,
                1L,
                timestamp,
                timestamp
        );
    }

    private MockMultipartFile image(String filename) {
        return new MockMultipartFile(
                "images",
                filename,
                "image/jpeg",
                new byte[]{1, 2, 3}
        );
    }
}
