from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(32) NOT NULL UNIQUE,
    "password_hash" VARCHAR(256) NOT NULL,
    "email" VARCHAR(32) NOT NULL UNIQUE,
    "verify" BOOL NOT NULL DEFAULT False,
    "register_time" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "login_time" TIMESTAMPTZ
);
COMMENT ON TABLE "user" IS 'User model';
CREATE TABLE IF NOT EXISTS "api_keys" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "key_hash" VARCHAR(256) NOT NULL,
    "prefix" VARCHAR(8) NOT NULL,
    "name" VARCHAR(64) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMPTZ,
    "is_active" BOOL NOT NULL DEFAULT True,
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "api_keys"."key_hash" IS 'Hashed API key';
COMMENT ON COLUMN "api_keys"."prefix" IS 'Key prefix for identification';
COMMENT ON COLUMN "api_keys"."name" IS 'Friendly name for the key';
COMMENT ON COLUMN "api_keys"."expires_at" IS 'Expiration time (optional)';
COMMENT ON COLUMN "api_keys"."is_active" IS 'Whether the key is active';
COMMENT ON COLUMN "api_keys"."user_id" IS 'Owner of the API key';
COMMENT ON TABLE "api_keys" IS 'API Key model for third-party access';
CREATE TABLE IF NOT EXISTS "requesttask" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(32) NOT NULL,
    "start_time" BIGINT,
    "request_url" VARCHAR(128) NOT NULL,
    "callback_url" VARCHAR(128),
    "callback_token" VARCHAR(64),
    "header" JSONB,
    "method" VARCHAR(10) NOT NULL DEFAULT 'GET',
    "body" JSONB NOT NULL,
    "message_id" VARCHAR(64),
    "cron" VARCHAR(64),
    "cron_count" INT NOT NULL DEFAULT 0,
    "job_id" VARCHAR(64),
    "status" VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    "error_message" TEXT,
    "response" JSONB,
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "requesttask" IS 'Request task model';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "LwMR22s="
)
