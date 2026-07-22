package com.blockai.roadbuddy.damage.service;

import com.blockai.roadbuddy.damage.domain.Damage;
import com.blockai.roadbuddy.damage.domain.DamageImage;
import com.blockai.roadbuddy.damage.domain.DamageSummary;
import com.blockai.roadbuddy.damage.mapper.DamageMapper;
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

    private MockMultipartFile image(String filename) {
        return new MockMultipartFile(
                "images",
                filename,
                "image/jpeg",
                new byte[]{1, 2, 3}
        );
    }
}
