CREATE TABLE IF NOT EXISTS application_reviews (
    application_id INTEGER PRIMARY KEY,
    plain_text TEXT NOT NULL,
    markdown TEXT NOT NULL,
    filename TEXT NOT NULL,
    summary_points TEXT NOT NULL DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_application_reviews_created_at
    ON application_reviews(created_at DESC);
