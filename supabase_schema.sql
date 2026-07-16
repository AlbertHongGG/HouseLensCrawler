-- ==============================================================================
-- HouseLens Supabase Database Schema & Tables
-- ==============================================================================

-- 1. Create dedicated schema
CREATE SCHEMA IF NOT EXISTS houselens;

-- 2. Create Builder Group table
CREATE TABLE IF NOT EXISTS houselens.builder_group (
    group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Create Builder table
CREATE TABLE IF NOT EXISTS houselens.builder (
    builder_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    group_id UUID REFERENCES houselens.builder_group(group_id) ON DELETE SET NULL,
    tax_id VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Create Community table
CREATE TABLE IF NOT EXISTS houselens.community (
    community_uuid VARCHAR(255) PRIMARY KEY, -- e.g., sinyi_0009465
    source_platform VARCHAR(50) NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500) NOT NULL,
    builder_id UUID REFERENCES houselens.builder(builder_id) ON DELETE SET NULL,
    builder_name_raw VARCHAR(255),
    completion_date VARCHAR(100),
    total_households INT,
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Create Property table
CREATE TABLE IF NOT EXISTS houselens.property (
    property_uuid VARCHAR(255) PRIMARY KEY,
    community_uuid VARCHAR(255) REFERENCES houselens.community(community_uuid) ON DELETE SET NULL,
    source_platform VARCHAR(50) NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    total_price NUMERIC,
    unit_price NUMERIC,
    building_ping NUMERIC,
    building_type VARCHAR(50),
    rooms INT,
    living_rooms INT,
    bathrooms INT,
    kitchens INT,
    balconies INT,
    age NUMERIC,
    floor VARCHAR(50),
    total_floor VARCHAR(50),
    address VARCHAR(500),
    url TEXT,
    has_parking BOOLEAN,
    parking_type VARCHAR(100),
    parking_ping NUMERIC,
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Create Crawler Dedup table
CREATE TABLE IF NOT EXISTS houselens.crawler_dedup (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_platform VARCHAR(50) NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'property' or 'community'
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source_platform, source_id, entity_type)
);

-- 7. Create Crawl Queue table
CREATE TABLE IF NOT EXISTS houselens.crawl_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spider_name VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, FAILED
    retry_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- Auto Mapping Triggers (Builder <-> Builder Group)
-- ==============================================================================

-- Trigger Function: Auto-assign group_id to a new builder based on group keywords
CREATE OR REPLACE FUNCTION houselens.match_builder_group_on_builder() 
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.group_id IS NULL THEN
        SELECT group_id INTO NEW.group_id
        FROM houselens.builder_group
        WHERE NEW.name LIKE ANY (
            SELECT '%' || unnest(keywords) || '%'
        )
        LIMIT 1;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_match_builder_group
BEFORE INSERT OR UPDATE ON houselens.builder
FOR EACH ROW
EXECUTE FUNCTION houselens.match_builder_group_on_builder();

-- Trigger Function: Update builders when a builder_group is updated
CREATE OR REPLACE FUNCTION houselens.update_builders_on_group_change() 
RETURNS TRIGGER AS $$
BEGIN
    UPDATE houselens.builder
    SET group_id = NEW.group_id
    WHERE name LIKE ANY (
        SELECT '%' || unnest(NEW.keywords) || '%'
    )
    AND (group_id IS NULL OR group_id = NEW.group_id OR group_id = OLD.group_id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_builders_on_group_change
AFTER INSERT OR UPDATE ON houselens.builder_group
FOR EACH ROW
EXECUTE FUNCTION houselens.update_builders_on_group_change();
