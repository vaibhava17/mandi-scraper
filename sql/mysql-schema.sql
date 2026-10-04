-- MySQL schema for the MySQL storage backend (DATABASE_URL=mysql://...).
-- Idempotent: safe to apply more than once. utf8mb4 for Indian-language text.
-- `mongo_id` is a 24-hex ObjectId-compatible id, so rows written by the MongoDB
-- backend and by the MySQL backend can live in the same tables.

CREATE TABLE IF NOT EXISTS mandi_prices (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  mongo_id      CHAR(24)      NOT NULL,
  arrival_date  DATE          NOT NULL,
  state         VARCHAR(60)   NOT NULL,
  district      VARCHAR(80)   NOT NULL,
  market        VARCHAR(150)  NOT NULL,
  commodity     VARCHAR(80)   NOT NULL,
  variety       VARCHAR(80)   NOT NULL,
  grade         VARCHAR(40)   DEFAULT NULL,
  min_price     DECIMAL(12,2) DEFAULT NULL,
  max_price     DECIMAL(12,2) DEFAULT NULL,
  modal_price   DECIMAL(12,2) DEFAULT NULL,
  price_per_kg  DECIMAL(12,3) DEFAULT NULL,
  source        VARCHAR(40)   DEFAULT NULL,
  created_at    DATETIME      DEFAULT NULL,
  updated_at    DATETIME      DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY u_mongo (mongo_id),
  UNIQUE KEY u_record (state, district, market, commodity, variety, arrival_date),
  KEY k_commodity_date (commodity, arrival_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=COMPRESSED;

CREATE TABLE IF NOT EXISTS nursery_plants (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  mongo_id      CHAR(24)      NOT NULL,
  scraped_date  DATE          NOT NULL,
  vendor        VARCHAR(100)  NOT NULL,
  name          VARCHAR(255)  NOT NULL,
  category      VARCHAR(60)   DEFAULT NULL,
  crop          VARCHAR(60)   DEFAULT NULL,
  variety       VARCHAR(120)  DEFAULT NULL,
  plant_stage   VARCHAR(60)   DEFAULT NULL,
  location      VARCHAR(120)  DEFAULT NULL,
  unit          VARCHAR(40)   DEFAULT NULL,
  currency      VARCHAR(8)    DEFAULT NULL,
  price         DECIMAL(12,2) DEFAULT NULL,
  price_min     DECIMAL(12,2) DEFAULT NULL,
  price_max     DECIMAL(12,2) DEFAULT NULL,
  product_url   VARCHAR(500)  DEFAULT NULL,
  source        VARCHAR(60)   DEFAULT NULL,
  created_at    DATETIME      DEFAULT NULL,
  updated_at    DATETIME      DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY u_mongo (mongo_id),
  UNIQUE KEY u_record (name, vendor, scraped_date),
  KEY k_cat_date (category, scraped_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=COMPRESSED;

CREATE TABLE IF NOT EXISTS seed_prices (
  id                 BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  mongo_id           CHAR(24)      NOT NULL,
  scraped_date       DATE          NOT NULL,
  vendor             VARCHAR(100)  NOT NULL,
  title              VARCHAR(255)  NOT NULL,
  brand              VARCHAR(100)  DEFAULT NULL,
  crop               VARCHAR(60)   DEFAULT NULL,
  variety            VARCHAR(255)  DEFAULT NULL,
  seed_type          VARCHAR(60)   DEFAULT NULL,
  pack_size          VARCHAR(60)   DEFAULT NULL,
  seed_rate_per_acre VARCHAR(60)   DEFAULT NULL,
  yield_potential    VARCHAR(100)  DEFAULT NULL,
  currency           VARCHAR(8)    DEFAULT NULL,
  price              DECIMAL(12,2) DEFAULT NULL,
  mrp                DECIMAL(12,2) DEFAULT NULL,
  product_url        VARCHAR(500)  DEFAULT NULL,
  source             VARCHAR(60)   DEFAULT NULL,
  created_at         DATETIME      DEFAULT NULL,
  updated_at         DATETIME      DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY u_mongo (mongo_id),
  UNIQUE KEY u_record (title, vendor, scraped_date),
  KEY k_crop_date (crop, scraped_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=COMPRESSED;

CREATE TABLE IF NOT EXISTS daily_summaries (
  date              DATE        NOT NULL,
  mongo_id          CHAR(24)    NOT NULL,
  total_mandi       INT         DEFAULT NULL,
  total_plants      INT         DEFAULT NULL,
  total_seeds       INT         DEFAULT NULL,
  mandi_highlights  JSON        DEFAULT NULL,
  text_summary      MEDIUMTEXT,
  updated_at        DATETIME    DEFAULT NULL,
  PRIMARY KEY (date),
  UNIQUE KEY u_mongo (mongo_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=COMPRESSED;
