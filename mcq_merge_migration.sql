-- ─────────────────────────────────────────────────────────────
-- MCQ DATABASE SCHEMA & DATA MERGE MIGRATION
-- Target Database: PostgreSQL (Supabase / AWS)
-- ─────────────────────────────────────────────────────────────

BEGIN;

-- Step 1: Add new choice and correctness columns to the ea_exam_eaquestion table if they do not exist
ALTER TABLE "ea_exam_eaquestion" ADD COLUMN IF NOT EXISTS "choice_1" varchar(500) DEFAULT '' NOT NULL;
ALTER TABLE "ea_exam_eaquestion" ALTER COLUMN "choice_1" DROP DEFAULT;

ALTER TABLE "ea_exam_eaquestion" ADD COLUMN IF NOT EXISTS "choice_1_correct" boolean DEFAULT false NOT NULL;
ALTER TABLE "ea_exam_eaquestion" ALTER COLUMN "choice_1_correct" DROP DEFAULT;

ALTER TABLE "ea_exam_eaquestion" ADD COLUMN IF NOT EXISTS "choice_2" varchar(500) DEFAULT '' NOT NULL;
ALTER TABLE "ea_exam_eaquestion" ALTER COLUMN "choice_2" DROP DEFAULT;

ALTER TABLE "ea_exam_eaquestion" ADD COLUMN IF NOT EXISTS "choice_2_correct" boolean DEFAULT false NOT NULL;
ALTER TABLE "ea_exam_eaquestion" ALTER COLUMN "choice_2_correct" DROP DEFAULT;

ALTER TABLE "ea_exam_eaquestion" ADD COLUMN IF NOT EXISTS "choice_3" varchar(500) DEFAULT '' NOT NULL;
ALTER TABLE "ea_exam_eaquestion" ALTER COLUMN "choice_3" DROP DEFAULT;

ALTER TABLE "ea_exam_eaquestion" ADD COLUMN IF NOT EXISTS "choice_3_correct" boolean DEFAULT false NOT NULL;
ALTER TABLE "ea_exam_eaquestion" ALTER COLUMN "choice_3_correct" DROP DEFAULT;

ALTER TABLE "ea_exam_eaquestion" ADD COLUMN IF NOT EXISTS "choice_4" varchar(500) DEFAULT '' NOT NULL;
ALTER TABLE "ea_exam_eaquestion" ALTER COLUMN "choice_4" DROP DEFAULT;

ALTER TABLE "ea_exam_eaquestion" ADD COLUMN IF NOT EXISTS "choice_4_correct" boolean DEFAULT false NOT NULL;
ALTER TABLE "ea_exam_eaquestion" ALTER COLUMN "choice_4_correct" DROP DEFAULT;


-- Step 2: Migrate data from ea_exam_eachoice to ea_exam_eaquestion columns
WITH OrderedChoices AS (
    SELECT 
        id,
        question_id,
        choice_text,
        is_correct,
        ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY "order", id) as rn
    FROM "ea_exam_eachoice"
),
ChoicesPivot AS (
    SELECT 
        question_id,
        MAX(CASE WHEN rn = 1 THEN choice_text END) as c1_text,
        MAX(CASE WHEN rn = 1 THEN is_correct END) as c1_correct,
        MAX(CASE WHEN rn = 2 THEN choice_text END) as c2_text,
        MAX(CASE WHEN rn = 2 THEN is_correct END) as c2_correct,
        MAX(CASE WHEN rn = 3 THEN choice_text END) as c3_text,
        MAX(CASE WHEN rn = 3 THEN is_correct END) as c3_correct,
        MAX(CASE WHEN rn = 4 THEN choice_text END) as c4_text,
        MAX(CASE WHEN rn = 4 THEN is_correct END) as c4_correct
    FROM OrderedChoices
    GROUP BY question_id
)
UPDATE "ea_exam_eaquestion" q
SET 
    choice_1 = COALESCE(p.c1_text, ''),
    choice_1_correct = COALESCE(p.c1_correct, false),
    choice_2 = COALESCE(p.c2_text, ''),
    choice_2_correct = COALESCE(p.c2_correct, false),
    choice_3 = COALESCE(p.c3_text, ''),
    choice_3_correct = COALESCE(p.c3_correct, false),
    choice_4 = COALESCE(p.c4_text, ''),
    choice_4_correct = COALESCE(p.c4_correct, false)
FROM ChoicesPivot p
WHERE q.id = p.question_id;


-- Step 3: Migrate historical session user answers in ea_exam_eaexamsession
-- This maps choice IDs (integers) to 'choice1'..'choice4' (strings) matching their order.
DO $$
DECLARE
    r RECORD;
    new_answers JSONB;
    key TEXT;
    val_text TEXT;
    choice_id INT;
    mapped_key TEXT;
BEGIN
    -- Only run this if the ea_exam_eaexamsession table exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables WHERE table_name='ea_exam_eaexamsession'
    ) THEN
        FOR r IN SELECT id, user_answers FROM "ea_exam_eaexamsession" WHERE user_answers IS NOT NULL LOOP
            new_answers := '{}'::jsonb;
            FOR key, val_text IN SELECT * FROM jsonb_each_text(r.user_answers) LOOP
                BEGIN
                    choice_id := val_text::int;
                    SELECT CASE rn
                        WHEN 1 THEN 'choice1'
                        WHEN 2 THEN 'choice2'
                        WHEN 3 THEN 'choice3'
                        WHEN 4 THEN 'choice4'
                        ELSE val_text
                    END INTO mapped_key
                    FROM (
                        SELECT id, ROW_NUMBER() OVER (ORDER BY "order", id) as rn
                        FROM "ea_exam_eachoice"
                        WHERE question_id = key::int
                    ) c
                    WHERE c.id = choice_id;
                    
                    IF mapped_key IS NOT NULL THEN
                        new_answers := jsonb_set(new_answers, ARRAY[key], to_jsonb(mapped_key));
                    ELSE
                        new_answers := jsonb_set(new_answers, ARRAY[key], to_jsonb(val_text));
                    END IF;
                EXCEPTION WHEN OTHERS THEN
                    new_answers := jsonb_set(new_answers, ARRAY[key], to_jsonb(val_text));
                END;
            END LOOP;
            
            UPDATE "ea_exam_eaexamsession"
            SET user_answers = new_answers
            WHERE id = r.id;
        END LOOP;
    END IF;
END $$;


-- Step 4: Drop the old ea_exam_eachoice table
DROP TABLE IF EXISTS "ea_exam_eachoice" CASCADE;

COMMIT;
