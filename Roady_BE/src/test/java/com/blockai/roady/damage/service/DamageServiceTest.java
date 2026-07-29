package com.blockai.roady.damage.service;

import com.blockai.roady.damage.domain.Damage;
import com.blockai.roady.damage.domain.DamageDashboardSummary;
import com.blockai.roady.damage.domain.DamageFilterCriteria;
import com.blockai.roady.damage.domain.DamageImage;
import com.blockai.roady.damage.domain.DamageSearchCriteria;
import com.blockai.roady.damage.domain.DamageSearchPage;
import com.blockai.roady.damage.domain.DamageStatusCount;
import com.blockai.roady.damage.domain.DamageSummary;
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

    @Mock
    private DamageMapper damageMapper;

    @InjectMocks
    private DamageService damageService;

    @Test
    void createStoresDamageAndMultipleImages() {
        LocalDateTime capturedAt = LocalDateTime.of(2026, 7, 22, 10, 30);
        MockMultipartFile firstImage = image("first.jpg");
        MockMultipartFile secondImage = image("second.jpg");

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
                "점자블록 파손",
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
                "점자블록 파손",
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

        List<DamageImage> savedImages = imageCaptor.getAllValues();
        assertThat(savedImages).extracting(DamageImage::getSortOrder).containsExactly(1, 2);
        assertThat(savedImages).extracting(DamageImage::getOriginalFilename)
                .containsExactly("first.jpg", "second.jpg");
        assertThat(result.imageCount()).isEqualTo(2L);
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
    }

    @Test
    void searchReturnsFilteredPage() {
        LocalDateTime from = LocalDateTime.of(2026, 7, 1, 0, 0);
        LocalDateTime to = LocalDateTime.of(2026, 8, 1, 0, 0);
        DamageSearchCriteria criteria = new DamageSearchCriteria(
                from,
                to,
                "REVIEW_REQUIRED",
                10L,
                3L,
                1,
                20
        );
        DamageSummary summary = new DamageSummary(
                1L,
                10L,
                2L,
                3L,
                "점자블록 파손",
                BigDecimal.valueOf(37.1234567),
                BigDecimal.valueOf(127.1234567),
                LocalDateTime.of(2026, 7, 22, 10, 30),
                "REVIEW_REQUIRED",
                2L,
                LocalDateTime.of(2026, 7, 22, 10, 31),
                LocalDateTime.of(2026, 7, 22, 10, 31)
        );

        when(damageMapper.searchSummaries(
                from,
                to,
                "REVIEW_REQUIRED",
                10L,
                3L,
                20L,
                20
        )).thenReturn(List.of(summary));
        when(damageMapper.countSummaries(
                from,
                to,
                "REVIEW_REQUIRED",
                10L,
                3L
        )).thenReturn(41L);

        DamageSearchPage result = damageService.search(criteria);

        assertThat(result.content()).containsExactly(summary);
        assertThat(result.page()).isEqualTo(1);
        assertThat(result.size()).isEqualTo(20);
        assertThat(result.totalElements()).isEqualTo(41);
        assertThat(result.totalPages()).isEqualTo(3);
    }

    @Test
    void searchCriteriaRejectsInvalidPageConditions() {
        assertThatThrownBy(() -> new DamageSearchCriteria(
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
                0,
                20
        )).isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Invalid damage status.");
    }

    @Test
    void summarizeReturnsTotalsAndZeroFilledStatusCounts() {
        LocalDateTime from = LocalDateTime.of(2026, 7, 1, 0, 0);
        LocalDateTime to = LocalDateTime.of(2026, 8, 1, 0, 0);
        DamageFilterCriteria criteria = new DamageFilterCriteria(from, to, null, 10L, null);
        when(damageMapper.summarizeByStatus(from, to, null, 10L, null))
                .thenReturn(List.of(
                        new DamageStatusCount("COLLECTED", 3, 2),
                        new DamageStatusCount("REVIEW_REQUIRED", 2, 1)
                ));

        DamageDashboardSummary result = damageService.summarize(criteria);

        assertThat(result.total()).isEqualTo(5);
        assertThat(result.unassigned()).isEqualTo(3);
        assertThat(result.statusCounts())
                .containsEntry("COLLECTED", 3L)
                .containsEntry("REVIEW_REQUIRED", 2L)
                .containsEntry("REPAIR_COMPLETED", 0L)
                .hasSize(7);
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
