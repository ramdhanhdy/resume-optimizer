-- Migration 004: Add linkedin_url and github_username columns to profiles table for cache lookup
-- This allows us to avoid re-scraping LinkedIn profiles on every pipeline run

ALTER TABLE profiles ADD COLUMN linkedin_url TEXT;
ALTER TABLE profiles ADD COLUMN github_username TEXT;

CREATE INDEX IF NOT EXISTS idx_profiles_linkedin ON profiles(linkedin_url);
CREATE INDEX IF NOT EXISTS idx_profiles_github ON profiles(github_username);
