"""initial schema

Revision ID: 20260526_0900
Revises: 
Create Date: 2026-05-26 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '20260526_0900'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute('''CREATE EXTENSION IF NOT EXISTS "pgcrypto";''')
    op.execute('''CREATE TYPE workspace_role AS ENUM ('admin', 'manager', 'member', 'viewer');''')
    op.execute('''CREATE TYPE project_visibility AS ENUM ('public', 'private');''')
    op.execute('''CREATE TYPE project_status AS ENUM ('active', 'archived');''')
    op.execute('''CREATE TYPE entry_status AS ENUM ('draft', 'running', 'pending', 'approved');''')
    op.execute('''CREATE TYPE submission_status AS ENUM ('pending', 'approved', 'rejected');''')
    op.execute('''CREATE TYPE rounding_mode AS ENUM ('none', 'nearest', 'up', 'down');''')
    op.execute('''CREATE TYPE webhook_event_type AS ENUM (
'time_entry.created',
'time_entry.updated',
'timesheet.submitted',
'timesheet.approved',
'timesheet.rejected'
);''')
    op.execute('''CREATE TYPE notification_event_type AS ENUM (
'timesheet_submitted',
'timesheet_approved',
'timesheet_rejected',
'timer_auto_stopped',
'workspace_deleted'
);''')
    op.execute('''CREATE TYPE audit_action AS ENUM (
'create', 'update', 'delete',
'approve', 'reject', 'submit',
'lock_override', 'role_change',
'invite_generated', 'invite_revoked',
'workspace_soft_deleted'
);''')
    op.execute('''CREATE TYPE webhook_delivery_status AS ENUM ('success', 'failed', 'retrying');''')
    op.execute('''CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
NEW.updated_at = NOW();
RETURN NEW;
END;
$$ LANGUAGE plpgsql;''')
    op.execute('''CREATE TABLE users (
id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
email             TEXT         NOT NULL UNIQUE,
password_hash     TEXT,
google_id         TEXT         UNIQUE,
full_name         TEXT         NOT NULL,
avatar_url        TEXT,
timezone          TEXT,
weekly_hours_goal SMALLINT     CHECK (weekly_hours_goal > 0),
is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);''')
    op.execute('''CREATE UNIQUE INDEX ix_users_email_lower ON users (LOWER(email));''')
    op.execute('''CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();''')
    op.execute('''CREATE TABLE password_reset_tokens (
id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
token       TEXT        NOT NULL UNIQUE,
expires_at  TIMESTAMPTZ NOT NULL DEFAULT NOW() + interval '1 hour',
used        BOOLEAN     NOT NULL DEFAULT FALSE,
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
CONSTRAINT chk_prt_expires CHECK (expires_at > created_at)
);''')
    op.execute('''CREATE INDEX ix_password_reset_tokens_user ON password_reset_tokens (user_id);''')
    op.execute('''CREATE TABLE workspaces (
id                          UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
name                        TEXT           NOT NULL,
logo_url                    TEXT,
default_timezone            TEXT           NOT NULL DEFAULT 'UTC',
date_format                 TEXT           NOT NULL DEFAULT 'MM/DD/YYYY'
CHECK (date_format IN ('MM/DD/YYYY','DD/MM/YYYY')),
currency                    CHAR(3)        NOT NULL DEFAULT 'USD',
default_hourly_rate_cents   BIGINT         CHECK (default_hourly_rate_cents >= 0),
rounding_mode               rounding_mode  NOT NULL DEFAULT 'none',
rounding_interval_minutes   SMALLINT       CHECK (rounding_interval_minutes IN (1,5,6,10,15,30)),
mandatory_description       BOOLEAN        NOT NULL DEFAULT FALSE,
max_timer_duration_seconds  INTEGER        NOT NULL DEFAULT 86400 CHECK (max_timer_duration_seconds > 0),
past_entry_limit_days       SMALLINT       NOT NULL DEFAULT 7 CHECK (past_entry_limit_days >= 0),
lock_period_days            SMALLINT       NOT NULL DEFAULT 7 CHECK (lock_period_days >= 0),
approval_workflow_enabled   BOOLEAN        NOT NULL DEFAULT FALSE,
idle_detection_enabled      BOOLEAN        NOT NULL DEFAULT FALSE,
idle_timeout_minutes        SMALLINT       CHECK (idle_timeout_minutes IN (1,2,5,10,15)),
deleted_at                  TIMESTAMPTZ,
created_at                  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
updated_at                  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
CONSTRAINT chk_ws_rounding CHECK (
rounding_mode = 'none' OR (rounding_mode != 'none' AND rounding_interval_minutes IS NOT NULL)
),
CONSTRAINT chk_ws_idle CHECK (
idle_detection_enabled = FALSE OR (idle_detection_enabled = TRUE AND idle_timeout_minutes IS NOT NULL)
)
);''')
    op.execute('''CREATE TRIGGER trg_workspaces_updated_at BEFORE UPDATE ON workspaces FOR EACH ROW EXECUTE FUNCTION set_updated_at();''')
    op.execute('''CREATE TABLE workspace_members (
workspace_id        UUID            NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
user_id             UUID            NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
role                workspace_role  NOT NULL DEFAULT 'member',
joined_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
invited_by_user_id  UUID            REFERENCES users(id) ON DELETE SET NULL,
PRIMARY KEY (workspace_id, user_id)
);''')
    op.execute('''CREATE INDEX ix_workspace_members_user ON workspace_members (user_id);''')
    op.execute('''CREATE TABLE invites (
id                 UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id       UUID            NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
email              TEXT            NOT NULL,
role               workspace_role  NOT NULL DEFAULT 'member'
CHECK (role IN ('manager','member','viewer')),
token              TEXT            NOT NULL UNIQUE,
expires_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW() + interval '7 days',
used               BOOLEAN         NOT NULL DEFAULT FALSE,
used_by_user_id    UUID            REFERENCES users(id) ON DELETE SET NULL,
used_at            TIMESTAMPTZ,
revoked            BOOLEAN         NOT NULL DEFAULT FALSE,
revoked_at         TIMESTAMPTZ,
created_by_user_id UUID            NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
created_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
CONSTRAINT chk_inv_expires      CHECK (expires_at > created_at),
CONSTRAINT chk_inv_used         CHECK ((used = TRUE AND used_at IS NOT NULL) OR (used = FALSE AND used_at IS NULL)),
CONSTRAINT chk_inv_revoked      CHECK ((revoked = TRUE AND revoked_at IS NOT NULL) OR (revoked = FALSE AND revoked_at IS NULL)),
CONSTRAINT chk_inv_not_both     CHECK (NOT (used = TRUE AND revoked = TRUE))
);''')
    op.execute('''CREATE UNIQUE INDEX ix_invites_token ON invites (token);''')
    op.execute('''CREATE INDEX ix_invites_workspace_expires ON invites (workspace_id, expires_at);''')
    op.execute('''CREATE TABLE clients (
id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id        UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
name                TEXT        NOT NULL,
email               TEXT,
phone               TEXT,
hourly_rate_cents   BIGINT      CHECK (hourly_rate_cents >= 0),
created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
UNIQUE (workspace_id, name)
);''')
    op.execute('''CREATE TRIGGER trg_clients_updated_at BEFORE UPDATE ON clients FOR EACH ROW EXECUTE FUNCTION set_updated_at();''')
    op.execute('''CREATE TABLE projects (
id                   UUID               PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id         UUID               NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
client_id            UUID               REFERENCES clients(id) ON DELETE SET NULL,
name                 TEXT               NOT NULL,
default_billable     BOOLEAN            NOT NULL DEFAULT TRUE,
budget_hours         NUMERIC(10,2)      CHECK (budget_hours > 0),
budget_amount_cents  BIGINT             CHECK (budget_amount_cents > 0),
visibility           project_visibility NOT NULL DEFAULT 'public',
status               project_status     NOT NULL DEFAULT 'active',
hourly_rate_cents    BIGINT             CHECK (hourly_rate_cents >= 0),
color                CHAR(7)            CHECK (color ~ '^#[0-9A-Fa-f]{6}$'),
archived_at          TIMESTAMPTZ,
created_at           TIMESTAMPTZ        NOT NULL DEFAULT NOW(),
updated_at           TIMESTAMPTZ        NOT NULL DEFAULT NOW(),
UNIQUE (workspace_id, name),
CONSTRAINT chk_proj_archived CHECK (
(status = 'archived' AND archived_at IS NOT NULL) OR
(status = 'active'   AND archived_at IS NULL)
)
);''')
    op.execute('''CREATE INDEX ix_projects_workspace_status ON projects (workspace_id, status);''')
    op.execute('''CREATE TRIGGER trg_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION set_updated_at();''')
    op.execute('''CREATE TABLE project_members (
project_id          UUID        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
user_id             UUID        NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
added_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
added_by_user_id    UUID        REFERENCES users(id) ON DELETE SET NULL,
PRIMARY KEY (project_id, user_id)
);''')
    op.execute('''CREATE TABLE tasks (
id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id        UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
project_id          UUID        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
name                TEXT        NOT NULL,
assignee_user_id    UUID        REFERENCES users(id) ON DELETE SET NULL,
estimated_hours     NUMERIC(8,2) CHECK (estimated_hours > 0),
billable_override   BOOLEAN,
hourly_rate_cents   BIGINT      CHECK (hourly_rate_cents >= 0),
created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
UNIQUE (project_id, name)
);''')
    op.execute('''CREATE INDEX ix_tasks_workspace ON tasks (workspace_id);''')
    op.execute('''CREATE INDEX ix_tasks_project ON tasks (project_id);''')
    op.execute('''CREATE TRIGGER trg_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION set_updated_at();''')
    op.execute('''CREATE TABLE tags (
id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
name         TEXT        NOT NULL,
color        CHAR(7)     CHECK (color ~ '^#[0-9A-Fa-f]{6}$'),
created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
UNIQUE (workspace_id, name)
);''')
    op.execute('''CREATE TABLE time_entries (
id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id          UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
user_id               UUID         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
project_id            UUID         NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
task_id               UUID         REFERENCES tasks(id) ON DELETE SET NULL,
description           TEXT,
billable              BOOLEAN      NOT NULL DEFAULT TRUE,
status                entry_status NOT NULL DEFAULT 'draft',
start_time            TIMESTAMPTZ  NOT NULL,
end_time              TIMESTAMPTZ,
duration_seconds      INTEGER      CHECK (duration_seconds >= 0),
hourly_rate_cents     BIGINT       CHECK (hourly_rate_cents >= 0),
billable_amount_cents BIGINT       CHECK (billable_amount_cents >= 0),
created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
CONSTRAINT chk_te_end_after_start  CHECK (end_time IS NULL OR end_time > start_time),
CONSTRAINT chk_te_running_no_end   CHECK (status != 'running' OR (end_time IS NULL AND duration_seconds IS NULL)),
CONSTRAINT chk_te_done_has_end     CHECK (status = 'running' OR status = 'draft' OR (end_time IS NOT NULL AND duration_seconds IS NOT NULL))
);''')
    op.execute('''CREATE UNIQUE INDEX uq_time_entries_one_running ON time_entries (user_id, workspace_id) WHERE status = 'running';''')
    op.execute('''CREATE INDEX ix_time_entries_user_start ON time_entries (user_id, start_time DESC);''')
    op.execute('''CREATE INDEX ix_time_entries_workspace_project ON time_entries (workspace_id, project_id);''')
    op.execute('''CREATE INDEX ix_time_entries_workspace_start ON time_entries (workspace_id, start_time DESC);''')
    op.execute('''CREATE INDEX ix_time_entries_workspace_status ON time_entries (workspace_id, status);''')
    op.execute('''CREATE TRIGGER trg_time_entries_updated_at BEFORE UPDATE ON time_entries FOR EACH ROW EXECUTE FUNCTION set_updated_at();''')
    op.execute('''CREATE TABLE time_entry_tags (
time_entry_id UUID NOT NULL REFERENCES time_entries(id) ON DELETE CASCADE,
tag_id        UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
PRIMARY KEY (time_entry_id, tag_id)
);''')
    op.execute('''CREATE TABLE timesheet_submissions (
id                  UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id        UUID              NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
user_id             UUID              NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
week_start          DATE              NOT NULL,
status              submission_status NOT NULL DEFAULT 'pending',
submitted_at        TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
reviewed_by_user_id UUID              REFERENCES users(id) ON DELETE SET NULL,
reviewed_at         TIMESTAMPTZ,
rejection_note      TEXT,
created_at          TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
updated_at          TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
CONSTRAINT chk_ts_week_is_monday    CHECK (EXTRACT(DOW FROM week_start) = 1),
CONSTRAINT chk_ts_rejection_note    CHECK (status != 'rejected' OR (rejection_note IS NOT NULL AND TRIM(rejection_note) != '')),
CONSTRAINT chk_ts_reviewed_at       CHECK ((status = 'pending' AND reviewed_at IS NULL) OR (status != 'pending' AND reviewed_at IS NOT NULL))
);''')
    op.execute('''CREATE UNIQUE INDEX uq_timesheet_submissions_one_pending
ON timesheet_submissions (workspace_id, user_id, week_start) WHERE status = 'pending';''')
    op.execute('''CREATE INDEX ix_timesheet_submissions_workspace_status ON timesheet_submissions (workspace_id, status);''')
    op.execute('''CREATE TRIGGER trg_timesheet_submissions_updated_at BEFORE UPDATE ON timesheet_submissions FOR EACH ROW EXECUTE FUNCTION set_updated_at();''')
    op.execute('''CREATE TABLE submission_entries (
submission_id  UUID NOT NULL REFERENCES timesheet_submissions(id) ON DELETE CASCADE,
time_entry_id  UUID NOT NULL REFERENCES time_entries(id) ON DELETE CASCADE,
PRIMARY KEY (submission_id, time_entry_id)
);''')
    op.execute('''CREATE UNIQUE INDEX uq_submission_entries_one_per_entry ON submission_entries (time_entry_id);''')
    op.execute('''CREATE TABLE saved_report_views (
id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
user_id      UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
name         TEXT        NOT NULL,
report_type  TEXT        NOT NULL CHECK (report_type IN ('summary','detailed')),
filters      JSONB       NOT NULL DEFAULT '{}',
created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
UNIQUE (workspace_id, user_id, name)
);''')
    op.execute('''CREATE TRIGGER trg_saved_report_views_updated_at BEFORE UPDATE ON saved_report_views FOR EACH ROW EXECUTE FUNCTION set_updated_at();''')
    op.execute('''CREATE TABLE webhooks (
id                UUID                 PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id      UUID                 NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
url               TEXT                 NOT NULL CHECK (url LIKE 'https://%'),
secret            TEXT,
subscribed_events webhook_event_type[] NOT NULL,
is_active         BOOLEAN              NOT NULL DEFAULT TRUE,
created_at        TIMESTAMPTZ          NOT NULL DEFAULT NOW(),
updated_at        TIMESTAMPTZ          NOT NULL DEFAULT NOW()
);''')
    op.execute('''CREATE TRIGGER trg_webhooks_updated_at BEFORE UPDATE ON webhooks FOR EACH ROW EXECUTE FUNCTION set_updated_at();''')
    op.execute('''CREATE TABLE webhook_delivery_logs (
id              UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
webhook_id      UUID                    NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
workspace_id    UUID                    NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
event_type      webhook_event_type      NOT NULL,
payload         JSONB                   NOT NULL,
attempt_number  SMALLINT                NOT NULL DEFAULT 1 CHECK (attempt_number BETWEEN 1 AND 3),
status          webhook_delivery_status NOT NULL DEFAULT 'retrying',
http_status_code SMALLINT,
response_body   TEXT,
error_message   TEXT,
attempted_at    TIMESTAMPTZ             NOT NULL DEFAULT NOW()
);''')
    op.execute('''CREATE INDEX ix_webhook_delivery_logs_webhook ON webhook_delivery_logs (webhook_id, attempted_at DESC);''')
    op.execute('''CREATE TABLE notifications (
id           UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id UUID                    NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
user_id      UUID                    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
event_type   notification_event_type NOT NULL,
title        TEXT                    NOT NULL,
message      TEXT                    NOT NULL,
metadata     JSONB,
read_at      TIMESTAMPTZ,
created_at   TIMESTAMPTZ             NOT NULL DEFAULT NOW()
);''')
    op.execute('''CREATE INDEX ix_notifications_user_workspace_read ON notifications (user_id, workspace_id, read_at);''')
    op.execute('''CREATE TABLE audit_logs (
id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
workspace_id  UUID         REFERENCES workspaces(id) ON DELETE SET NULL,
actor_user_id UUID         REFERENCES users(id) ON DELETE SET NULL,
action        audit_action NOT NULL,
entity_type   TEXT         NOT NULL,
entity_id     UUID,
old_values    JSONB,
new_values    JSONB,
ip_address    INET,
user_agent    TEXT,
created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);''')
    op.execute('''CREATE INDEX ix_audit_logs_workspace_created ON audit_logs (workspace_id, created_at DESC);''')
    op.execute('''CREATE INDEX ix_audit_logs_actor_created ON audit_logs (actor_user_id, created_at DESC);''')
    op.execute('''CREATE INDEX ix_audit_logs_entity ON audit_logs (entity_type, entity_id);''')


def downgrade() -> None:

    op.execute('DROP TABLE IF EXISTS audit_logs CASCADE')
    op.execute('DROP TABLE IF EXISTS notifications CASCADE')
    op.execute('DROP TABLE IF EXISTS webhook_delivery_logs CASCADE')
    op.execute('DROP TABLE IF EXISTS webhooks CASCADE')
    op.execute('DROP TABLE IF EXISTS saved_report_views CASCADE')
    op.execute('DROP TABLE IF EXISTS submission_entries CASCADE')
    op.execute('DROP TABLE IF EXISTS timesheet_submissions CASCADE')
    op.execute('DROP TABLE IF EXISTS time_entry_tags CASCADE')
    op.execute('DROP TABLE IF EXISTS time_entries CASCADE')
    op.execute('DROP TABLE IF EXISTS tags CASCADE')
    op.execute('DROP TABLE IF EXISTS tasks CASCADE')
    op.execute('DROP TABLE IF EXISTS project_members CASCADE')
    op.execute('DROP TABLE IF EXISTS projects CASCADE')
    op.execute('DROP TABLE IF EXISTS clients CASCADE')
    op.execute('DROP TABLE IF EXISTS invites CASCADE')
    op.execute('DROP TABLE IF EXISTS workspace_members CASCADE')
    op.execute('DROP TABLE IF EXISTS workspaces CASCADE')
    op.execute('DROP TABLE IF EXISTS password_reset_tokens CASCADE')
    op.execute('DROP TABLE IF EXISTS users CASCADE')

    op.execute('DROP FUNCTION IF EXISTS set_updated_at CASCADE')

    op.execute('DROP TYPE IF EXISTS webhook_delivery_status CASCADE')
    op.execute('DROP TYPE IF EXISTS audit_action CASCADE')
    op.execute('DROP TYPE IF EXISTS notification_event_type CASCADE')
    op.execute('DROP TYPE IF EXISTS webhook_event_type CASCADE')
    op.execute('DROP TYPE IF EXISTS rounding_mode CASCADE')
    op.execute('DROP TYPE IF EXISTS submission_status CASCADE')
    op.execute('DROP TYPE IF EXISTS entry_status CASCADE')
    op.execute('DROP TYPE IF EXISTS project_status CASCADE')
    op.execute('DROP TYPE IF EXISTS project_visibility CASCADE')
    op.execute('DROP TYPE IF EXISTS workspace_role CASCADE')

    op.execute('DROP EXTENSION IF EXISTS "pgcrypto" CASCADE')
    