BEGIN;

ALTER TABLE "user" ADD COLUMN gdpr_agreed TIMESTAMP WITH TIME ZONE;

COMMIT;

