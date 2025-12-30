-- Migration 003: Add job_url column to applications table
-- This allows tracking the original job posting URL for deduplication and reference

ALTER TABLE applications ADD COLUMN job_url TEXT;
