package com.blockai.roady.statistics;

import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;

class StatisticsIndexScriptTest {

    @Test
    void schemaAndMigrationDeclareStatisticsIndexes() throws IOException {
        String schema = Files.readString(Path.of("src/main/resources/rdb/schema.sql"));
        String migration = Files.readString(Path.of("docs/sql/statistics-indexes.sql"));

        assertThat(schema)
                .contains("idx_damages_statistics_created_status")
                .contains("idx_damage_ai_damage_status_created_id");
        assertThat(migration)
                .contains("idx_damages_statistics_created_status")
                .contains("idx_damage_ai_damage_status_created_id");
    }
}
