package com.blockai.roady.damage.domain;

import java.time.LocalDateTime;

public class DamageImage {

    private Long id;
    private Long damageId;
    private int sortOrder;
    private String originalFilename;
    private String contentType;
    private long sizeBytes;
    private byte[] data;
    private LocalDateTime createdAt;

    public DamageImage() {
    }

    public DamageImage(
            Long id,
            Long damageId,
            int sortOrder,
            String originalFilename,
            String contentType,
            long sizeBytes,
            byte[] data,
            LocalDateTime createdAt
    ) {
        this.id = id;
        this.damageId = damageId;
        this.sortOrder = sortOrder;
        this.originalFilename = originalFilename;
        this.contentType = contentType;
        this.sizeBytes = sizeBytes;
        this.data = data;
        this.createdAt = createdAt;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getDamageId() {
        return damageId;
    }

    public void setDamageId(Long damageId) {
        this.damageId = damageId;
    }

    public int getSortOrder() {
        return sortOrder;
    }

    public void setSortOrder(int sortOrder) {
        this.sortOrder = sortOrder;
    }

    public String getOriginalFilename() {
        return originalFilename;
    }

    public void setOriginalFilename(String originalFilename) {
        this.originalFilename = originalFilename;
    }

    public String getContentType() {
        return contentType;
    }

    public void setContentType(String contentType) {
        this.contentType = contentType;
    }

    public long getSizeBytes() {
        return sizeBytes;
    }

    public void setSizeBytes(long sizeBytes) {
        this.sizeBytes = sizeBytes;
    }

    public byte[] getData() {
        return data;
    }

    public void setData(byte[] data) {
        this.data = data;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
