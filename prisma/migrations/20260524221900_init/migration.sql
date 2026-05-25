-- CreateTable
CREATE TABLE `kino_draws` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `draw_number` INTEGER NOT NULL,
    `draw_date` DATE NOT NULL,
    `draw_day` ENUM('wednesday', 'friday', 'sunday') NOT NULL,
    `numbers` JSON NOT NULL,
    `adicional` INTEGER NULL,
    `prize_jackpot` BIGINT NULL,
    `winners_count` INTEGER NULL,
    `source_url` VARCHAR(500) NULL,
    `scraped_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    UNIQUE INDEX `kino_draws_draw_number_key`(`draw_number`),
    INDEX `kino_draws_draw_date_idx`(`draw_date`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `loto_draws` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `draw_number` INTEGER NOT NULL,
    `draw_date` DATE NOT NULL,
    `draw_day` ENUM('tuesday', 'thursday', 'sunday') NOT NULL,
    `numbers` JSON NOT NULL,
    `revancha` JSON NULL,
    `desquite` JSON NULL,
    `prize_jackpot` BIGINT NULL,
    `winners_count` INTEGER NULL,
    `source_url` VARCHAR(500) NULL,
    `scraped_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    UNIQUE INDEX `loto_draws_draw_number_key`(`draw_number`),
    INDEX `loto_draws_draw_date_idx`(`draw_date`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `statistics_cache` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `game` ENUM('kino', 'loto') NOT NULL,
    `stat_type` VARCHAR(100) NOT NULL,
    `time_window` VARCHAR(50) NOT NULL DEFAULT 'all',
    `data` JSON NOT NULL,
    `computed_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    UNIQUE INDEX `statistics_cache_game_stat_type_time_window_key`(`game`, `stat_type`, `time_window`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `scraper_logs` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `game` ENUM('kino', 'loto') NOT NULL,
    `status` ENUM('success', 'error', 'no_new_data') NOT NULL,
    `draws_found` INTEGER NOT NULL DEFAULT 0,
    `message` TEXT NULL,
    `run_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    INDEX `scraper_logs_run_at_idx`(`run_at`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
