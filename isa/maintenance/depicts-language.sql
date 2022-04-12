-- Add column for depicts language for user settings. Introduced in
-- https://phabricator.wikimedia.org/T252232.
ALTER TABLE user ADD depicts_language varchar(13) NOT NULL;
