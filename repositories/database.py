from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterable

import pandas as pd

from core.paths import DB_PATH, ensure_dirs

DEFAULT_EVENT_NAME = "Evento Principal"

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(trim(name)) > 0),
    date TEXT,
    location TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    original_name TEXT,
    category TEXT,
    type TEXT,
    group_name TEXT,
    invitation_type TEXT DEFAULT 'individual',
    invitation_label TEXT,
    current_table TEXT,
    corrected_table TEXT,
    final_table TEXT,
    table_status TEXT,
    phone TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_guests_event ON guests(event_id);
CREATE INDEX IF NOT EXISTS idx_guests_event_group ON guests(event_id, group_name);
CREATE INDEX IF NOT EXISTS idx_guests_event_table ON guests(event_id, final_table);

CREATE TABLE IF NOT EXISTS tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    capacity INTEGER CHECK(capacity IS NULL OR capacity >= 0),
    observation TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, name),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tables_event ON tables(event_id);

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    phone TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, name),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_groups_event ON groups(event_id);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    guest_id INTEGER,
    group_name TEXT,
    guest_name TEXT,
    phone TEXT,
    table_name TEXT,
    template TEXT,
    message_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','sent','error')),
    error TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    sent_at TEXT,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(guest_id) REFERENCES guests(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_event_status ON messages(event_id, status);
CREATE INDEX IF NOT EXISTS idx_messages_event_guest_status ON messages(event_id, guest_id, status);

CREATE TABLE IF NOT EXISTS message_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    message_id INTEGER,
    status TEXT NOT NULL CHECK(status IN ('pending','sent','error','preview')),
    detail TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    source_file TEXT,
    total_records INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    detail TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS import_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    import_id INTEGER,
    source TEXT,
    total_records INTEGER DEFAULT 0,
    imported_count INTEGER DEFAULT 0,
    invalid_count INTEGER DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    detail TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(import_id) REFERENCES imports(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    area TEXT NOT NULL,
    error_message TEXT NOT NULL,
    detail TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    area TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'INFO',
    message TEXT NOT NULL,
    detail TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
"""


PREMIUM_SCHEMA = """
CREATE TABLE IF NOT EXISTS guest_rsvp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    guest_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','confirmed','declined','maybe')),
    source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('manual','whatsapp','import','assessoria_vip')),
    notes TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, guest_id),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(guest_id) REFERENCES guests(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_rsvp_event_status ON guest_rsvp(event_id, status);

CREATE TABLE IF NOT EXISTS guest_checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    guest_id INTEGER NOT NULL,
    checked_in INTEGER NOT NULL DEFAULT 0 CHECK(checked_in IN (0,1)),
    checked_in_at TEXT,
    method TEXT NOT NULL DEFAULT 'manual' CHECK(method IN ('manual','qr_code','import')),
    notes TEXT,
    UNIQUE(event_id, guest_id),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(guest_id) REFERENCES guests(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_checkins_event_checked ON guest_checkins(event_id, checked_in);

CREATE TABLE IF NOT EXISTS event_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    title TEXT NOT NULL CHECK(length(trim(title)) > 0),
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','in_progress','done','canceled')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low','medium','high','critical')),
    due_date TEXT,
    owner TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tasks_event_status ON event_tasks(event_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_event_priority ON event_tasks(event_id, priority);

CREATE TABLE IF NOT EXISTS event_timeline_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    title TEXT NOT NULL CHECK(length(trim(title)) > 0),
    description TEXT,
    owner TEXT,
    status TEXT NOT NULL DEFAULT 'planned' CHECK(status IN ('planned','running','done','delayed')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_timeline_event_time ON event_timeline_items(event_id, time);
CREATE INDEX IF NOT EXISTS idx_timeline_event_status ON event_timeline_items(event_id, status);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_audit_event_created ON audit_logs(event_id, created_at);
"""


INTELLIGENCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS guest_score (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    guest_id INTEGER NOT NULL,
    attendance_probability REAL NOT NULL DEFAULT 0 CHECK(attendance_probability >= 0 AND attendance_probability <= 1),
    priority_score REAL NOT NULL DEFAULT 0 CHECK(priority_score >= 0 AND priority_score <= 100),
    engagement_score REAL NOT NULL DEFAULT 0 CHECK(engagement_score >= 0 AND engagement_score <= 100),
    explanation TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, guest_id),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(guest_id) REFERENCES guests(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_guest_score_event ON guest_score(event_id);

CREATE TABLE IF NOT EXISTS automation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL CHECK(length(trim(name)) > 0),
    trigger TEXT NOT NULL CHECK(trigger IN ('RSVP_confirmed','RSVP_pending','event_minus_3_days','event_minus_1_day','checkin_missing')),
    action TEXT NOT NULL CHECK(action IN ('send_message','reminder','create_task')),
    condition TEXT,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
    template TEXT,
    target_status TEXT,
    last_run_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_automation_rules_event ON automation_rules(event_id, enabled);

CREATE TABLE IF NOT EXISTS automation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    rule_id INTEGER,
    status TEXT NOT NULL CHECK(status IN ('success','partial_success','error','dry_run')),
    processed_count INTEGER DEFAULT 0,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(rule_id) REFERENCES automation_rules(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_automation_runs_event ON automation_runs(event_id, created_at);
"""


ADAPTIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS adaptive_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    weight_name TEXT NOT NULL,
    weight_value REAL NOT NULL DEFAULT 1,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, weight_name),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_adaptive_weights_event ON adaptive_weights(event_id);

CREATE TABLE IF NOT EXISTS event_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL UNIQUE,
    confirmation_rate REAL NOT NULL DEFAULT 0,
    presence_rate REAL NOT NULL DEFAULT 0,
    no_show_rate REAL NOT NULL DEFAULT 0,
    avg_attendance_probability REAL NOT NULL DEFAULT 0,
    dominant_groups TEXT,
    operational_risk TEXT NOT NULL DEFAULT 'low' CHECK(operational_risk IN ('low','medium','high','critical')),
    learned_notes TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS intelligent_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info' CHECK(severity IN ('info','warning','critical')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    action_suggestion TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_intelligent_insights_event ON intelligent_insights(event_id, created_at);

CREATE TABLE IF NOT EXISTS orchestrator_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    decision_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'executed' CHECK(status IN ('executed','skipped','error','dry_run')),
    summary TEXT NOT NULL,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_orchestrator_decisions_event ON orchestrator_decisions(event_id, created_at);
"""



COMPETITIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS global_event_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL UNIQUE,
    event_name TEXT,
    event_date TEXT,
    location TEXT,
    total_guests INTEGER NOT NULL DEFAULT 0,
    confirmation_rate REAL NOT NULL DEFAULT 0,
    presence_rate REAL NOT NULL DEFAULT 0,
    no_show_rate REAL NOT NULL DEFAULT 0,
    table_efficiency REAL NOT NULL DEFAULT 0,
    avg_attendance_probability REAL NOT NULL DEFAULT 0,
    critical_conflicts INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'adaptive_engine',
    snapshot_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_global_event_insights_updated ON global_event_insights(updated_at);

CREATE TABLE IF NOT EXISTS guest_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    guest_id INTEGER NOT NULL,
    behavioral_type TEXT NOT NULL DEFAULT 'unknown' CHECK(behavioral_type IN ('champion','reliable','needs_followup','at_risk','declined','unknown')),
    attendance_pattern TEXT NOT NULL DEFAULT 'unknown' CHECK(attendance_pattern IN ('always_present','confirmed_present','confirmed_absent','uncertain','declined','unknown')),
    influence_score REAL NOT NULL DEFAULT 0 CHECK(influence_score >= 0 AND influence_score <= 100),
    profile_notes TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, guest_id),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(guest_id) REFERENCES guests(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_guest_profile_event_type ON guest_profile(event_id, behavioral_type);

CREATE TABLE IF NOT EXISTS proactive_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low','medium','high','critical')),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'suggested' CHECK(status IN ('suggested','accepted','dismissed','done')),
    payload_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_proactive_actions_event_status ON proactive_actions(event_id, status, priority);
"""



PORTAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS guest_public_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    guest_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expires_at TEXT,
    used_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, guest_id),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(guest_id) REFERENCES guests(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_guest_public_links_event ON guest_public_links(event_id);
CREATE INDEX IF NOT EXISTS idx_guest_public_links_token ON guest_public_links(token);

CREATE TABLE IF NOT EXISTS guest_portal_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    guest_id INTEGER NOT NULL,
    link_id INTEGER,
    confirm_presence TEXT NOT NULL DEFAULT 'pending' CHECK(confirm_presence IN ('pending','confirmed','declined','maybe')),
    needs_bus INTEGER NOT NULL DEFAULT 0 CHECK(needs_bus IN (0,1)),
    bus_pickup_point TEXT,
    companions_count INTEGER NOT NULL DEFAULT 0 CHECK(companions_count >= 0),
    dietary_restrictions TEXT,
    notes TEXT,
    phone TEXT,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, guest_id),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(guest_id) REFERENCES guests(id) ON DELETE CASCADE,
    FOREIGN KEY(link_id) REFERENCES guest_public_links(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_guest_portal_responses_event ON guest_portal_responses(event_id);
CREATE INDEX IF NOT EXISTS idx_guest_portal_responses_bus ON guest_portal_responses(event_id, needs_bus);
"""


CRM_SCHEMA = """
CREATE TABLE IF NOT EXISTS event_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    guest_id INTEGER,
    name TEXT NOT NULL CHECK(length(trim(name)) > 0),
    phone TEXT NOT NULL,
    email TEXT,
    group_name TEXT,
    source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('manual','excel','csv','vcf','pdf','portal')),
    tags TEXT,
    notes TEXT,
    is_valid INTEGER NOT NULL DEFAULT 1 CHECK(is_valid IN (0,1)),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, phone),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(guest_id) REFERENCES guests(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_event_contacts_event ON event_contacts(event_id);
CREATE INDEX IF NOT EXISTS idx_event_contacts_event_phone ON event_contacts(event_id, phone);
CREATE INDEX IF NOT EXISTS idx_event_contacts_event_group ON event_contacts(event_id, group_name);

CREATE TABLE IF NOT EXISTS whatsapp_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL CHECK(length(trim(name)) > 0),
    template TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','queued','running','done','partial_error','error','canceled')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_whatsapp_campaigns_event ON whatsapp_campaigns(event_id, created_at);

CREATE TABLE IF NOT EXISTS whatsapp_campaign_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    campaign_id INTEGER NOT NULL,
    contact_id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    message_text TEXT,
    message_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','sent','error','skipped')),
    error_message TEXT,
    sent_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, campaign_id, contact_id),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(campaign_id) REFERENCES whatsapp_campaigns(id) ON DELETE CASCADE,
    FOREIGN KEY(contact_id) REFERENCES event_contacts(id) ON DELETE CASCADE,
    FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_campaign_recipients_event_status ON whatsapp_campaign_recipients(event_id, status);
CREATE INDEX IF NOT EXISTS idx_campaign_recipients_campaign_status ON whatsapp_campaign_recipients(campaign_id, status);
"""


SAAS_PATCH_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT 'Usuário',
    email TEXT UNIQUE,
    role TEXT NOT NULL DEFAULT 'ADMIN' CHECK(role IN ('ADMIN','CLIENT','STAFF')),
    event_id INTEGER,
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_users_role_event ON users(role, event_id);

CREATE TABLE IF NOT EXISTS event_forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_event_forms_event ON event_forms(event_id);

CREATE TABLE IF NOT EXISTS event_form_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('text','select','boolean')),
    required INTEGER NOT NULL DEFAULT 0 CHECK(required IN (0,1)),
    options TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(form_id) REFERENCES event_forms(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_form_fields_form ON event_form_fields(form_id, sort_order);

CREATE TABLE IF NOT EXISTS event_form_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_id INTEGER NOT NULL,
    field_id INTEGER NOT NULL,
    value TEXT,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guest_id, field_id),
    FOREIGN KEY(guest_id) REFERENCES guests(id) ON DELETE CASCADE,
    FOREIGN KEY(field_id) REFERENCES event_form_fields(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_form_responses_guest ON event_form_responses(guest_id);

CREATE TABLE IF NOT EXISTS message_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, name),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    phone TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_vendors_event ON vendors(event_id);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    vendor_id INTEGER,
    description TEXT,
    amount REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('paid','pending','overdue','canceled')),
    due_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(vendor_id) REFERENCES vendors(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_expenses_event_status ON expenses(event_id, status);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    paid_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(expense_id) REFERENCES expenses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_documents_event ON event_documents(event_id, uploaded_at);
"""



PRODUCTION_SAAS_SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS background_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER,
    event_id INTEGER,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','success','failed','canceled')),
    progress INTEGER NOT NULL DEFAULT 0,
    retries INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT,
    started_at TEXT,
    finished_at TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE SET NULL,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON background_jobs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_tenant_status ON background_jobs(tenant_id, status);

CREATE TABLE IF NOT EXISTS exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER,
    event_id INTEGER,
    export_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ready',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE SET NULL,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_exports_event_type ON exports(event_id, export_type);
"""


SAAS_ADVANCED_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TEXT,
    revoked_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE SET NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_refresh_user_active ON api_refresh_tokens(user_id, revoked_at);

CREATE TABLE IF NOT EXISTS automation_rule_advanced (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    event_id INTEGER,
    trigger_type TEXT NOT NULL,
    condition_json TEXT,
    action_type TEXT NOT NULL,
    action_json TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    last_run_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_automation_adv_tenant_active ON automation_rule_advanced(tenant_id, is_active);

CREATE TABLE IF NOT EXISTS automation_run_advanced (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'success' CHECK(status IN ('success','failed','skipped','running')),
    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    result_json TEXT,
    FOREIGN KEY(rule_id) REFERENCES automation_rule_advanced(id) ON DELETE CASCADE,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_automation_run_adv_rule ON automation_run_advanced(rule_id, executed_at);

CREATE TABLE IF NOT EXISTS onboarding_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL UNIQUE,
    current_step INTEGER NOT NULL DEFAULT 1,
    tenant_created INTEGER NOT NULL DEFAULT 0,
    event_created INTEGER NOT NULL DEFAULT 0,
    guests_imported INTEGER NOT NULL DEFAULT 0,
    form_created INTEGER NOT NULL DEFAULT 0,
    first_campaign_sent INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scheduled_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    campaign_id INTEGER,
    scheduled_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled','running','sent','failed','canceled')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_scheduled_campaigns_status ON scheduled_campaigns(status, scheduled_at);
"""

STATUS_ALIASES = {
    "pendente": "pending",
    "enviado": "sent",
    "erro": "error",
    "todos": "todos",
    "pending": "pending",
    "sent": "sent",
    "error": "error",
    "preview": "preview",
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


PRODUCTION_CONSOLIDATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    refresh_token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_active ON user_sessions(user_id, revoked_at, expires_at);

CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL DEFAULT 1,
    event_id INTEGER NOT NULL,
    snapshot_date TEXT NOT NULL,
    total_guests INTEGER NOT NULL DEFAULT 0,
    confirmed_guests INTEGER NOT NULL DEFAULT 0,
    pending_guests INTEGER NOT NULL DEFAULT 0,
    declined_guests INTEGER NOT NULL DEFAULT 0,
    messages_sent INTEGER NOT NULL DEFAULT 0,
    messages_failed INTEGER NOT NULL DEFAULT 0,
    expenses_total REAL NOT NULL DEFAULT 0,
    expenses_paid REAL NOT NULL DEFAULT 0,
    tables_occupancy_rate REAL NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, event_id, snapshot_date),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_snapshots_event_date ON analytics_snapshots(event_id, snapshot_date);
"""

@contextmanager
def connect():
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    except sqlite3.OperationalError:
        return set()


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    if column not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def normalize_status(status: str | None) -> str | None:
    if status is None:
        return None
    return STATUS_ALIASES.get(str(status).strip().lower(), str(status).strip().lower())


def ensure_default_event(conn: sqlite3.Connection | None = None) -> int:
    ensure_dirs()
    own = conn is None
    if own:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, date TEXT, location TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    assert conn is not None
    row = conn.execute("SELECT id FROM events ORDER BY id LIMIT 1").fetchone()
    if row:
        event_id = int(row["id"])
    else:
        cur = conn.execute("INSERT INTO events(name, date, location) VALUES (?, ?, ?)", (DEFAULT_EVENT_NAME, "", ""))
        event_id = int(cur.lastrowid)
    if own:
        conn.commit()
        conn.close()
    return event_id


def _safe_event_id(event_id: int | None, conn: sqlite3.Connection | None = None) -> int:
    return int(event_id) if event_id else ensure_default_event(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    default_id = ensure_default_event(conn)
    for table in ["guests", "tables", "groups", "messages", "imports", "message_logs", "import_logs", "error_logs", "app_logs"]:
        _add_column_if_missing(conn, table, "event_id", "INTEGER")
        conn.execute(f"UPDATE {table} SET event_id=? WHERE event_id IS NULL", (default_id,))
    _add_column_if_missing(conn, "messages", "guest_id", "INTEGER")
    _add_column_if_missing(conn, "guests", "invitation_type", "TEXT DEFAULT 'individual'")
    _add_column_if_missing(conn, "guests", "invitation_label", "TEXT")
    conn.execute(
        """
        UPDATE guests
        SET invitation_type=CASE
            WHEN COALESCE(group_name, '') <> '' THEN 'family'
            ELSE 'individual'
        END
        WHERE invitation_type IS NULL OR invitation_type=''
        """
    )
    conn.execute(
        """
        UPDATE guests
        SET invitation_label=COALESCE(NULLIF(group_name, ''), name)
        WHERE invitation_label IS NULL OR invitation_label=''
        """
    )
    for column, definition in {
        "source": "TEXT",
        "total_records": "INTEGER DEFAULT 0",
        "imported_count": "INTEGER DEFAULT 0",
        "invalid_count": "INTEGER DEFAULT 0",
        "duplicate_count": "INTEGER DEFAULT 0",
        "skipped_count": "INTEGER DEFAULT 0",
    }.items():
        _add_column_if_missing(conn, "import_logs", column, definition)
    _add_column_if_missing(conn, "whatsapp_campaign_recipients", "message_id", "INTEGER")
    _add_column_if_missing(conn, "users", "role", "TEXT NOT NULL DEFAULT 'ADMIN'")
    _add_column_if_missing(conn, "message_logs", "guest_id", "INTEGER")
    _add_column_if_missing(conn, "message_logs", "error_message", "TEXT")
    _add_column_if_missing(conn, "message_logs", "retries", "INTEGER NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "message_logs", "sent_at", "TEXT")
    _add_column_if_missing(conn, "message_logs", "provider", "TEXT")
    _add_column_if_missing(conn, "message_logs", "request_payload", "TEXT")
    _add_column_if_missing(conn, "message_logs", "response_status_code", "INTEGER")
    _add_column_if_missing(conn, "message_logs", "response_body", "TEXT")
    _add_column_if_missing(conn, "message_logs", "attempt_number", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(conn, "event_forms", "is_active", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(conn, "event_forms", "active", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(conn, "event_form_fields", "is_active", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(conn, "event_documents", "original_filename", "TEXT")
    _add_column_if_missing(conn, "event_documents", "stored_filename", "TEXT")
    _add_column_if_missing(conn, "event_documents", "category", "TEXT DEFAULT 'outro'")
    _add_column_if_missing(conn, "event_documents", "description", "TEXT")
    _add_column_if_missing(conn, "event_documents", "vendor_id", "INTEGER")
    _add_column_if_missing(conn, "event_documents", "is_deleted", "INTEGER NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "vendors", "phone", "TEXT")
    _add_column_if_missing(conn, "vendors", "notes", "TEXT")
    _add_column_if_missing(conn, "expenses", "paid_at", "TEXT")
    _add_column_if_missing(conn, "expenses", "receipt_path", "TEXT")
    _add_column_if_missing(conn, "expenses", "category", "TEXT")

    # Produção/SaaS: colunas adicionadas de forma incremental para preservar SQLite atual.
    for table in ["events", "guests", "event_forms", "event_documents", "vendors", "expenses", "messages", "message_templates", "whatsapp_campaigns", "whatsapp_campaign_recipients"]:
        _add_column_if_missing(conn, table, "tenant_id", "INTEGER")
    _add_column_if_missing(conn, "users", "tenant_id", "INTEGER")
    _add_column_if_missing(conn, "users", "password_hash", "TEXT")
    _add_column_if_missing(conn, "users", "is_active", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(conn, "users", "active", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(conn, "audit_logs", "tenant_id", "INTEGER")
    _add_column_if_missing(conn, "audit_logs", "user_id", "INTEGER")
    _add_column_if_missing(conn, "audit_logs", "metadata_json", "TEXT")
    _add_column_if_missing(conn, "audit_logs", "details", "TEXT")
    _add_column_if_missing(conn, "audit_logs", "ip", "TEXT")
    _add_column_if_missing(conn, "audit_logs", "user_agent", "TEXT")
    _add_column_if_missing(conn, "audit_logs", "request_id", "TEXT")
    _add_column_if_missing(conn, "audit_logs", "severity", "TEXT DEFAULT 'info'")

    conn.execute("INSERT OR IGNORE INTO tenants(id, name, slug) VALUES (1, 'Assessoria Demo', 'assessoria-demo')")
    for table in ["events", "guests", "event_forms", "event_documents", "vendors", "expenses", "messages", "message_templates", "whatsapp_campaigns", "whatsapp_campaign_recipients", "users"]:
        try:
            conn.execute(f"UPDATE {table} SET tenant_id=1 WHERE tenant_id IS NULL")
        except sqlite3.OperationalError:
            pass

    conn.execute("UPDATE event_forms SET is_active=COALESCE(is_active, active, 1), active=COALESCE(active, is_active, 1)")
    conn.execute("UPDATE event_form_fields SET is_active=1 WHERE is_active IS NULL")
    conn.execute("UPDATE event_documents SET original_filename=COALESCE(original_filename, name), stored_filename=COALESCE(stored_filename, name) WHERE original_filename IS NULL OR stored_filename IS NULL")

    try:
        from services.security_service import hash_password
        admin_hash = hash_password('admin123')
        conn.execute("INSERT OR IGNORE INTO users(id, tenant_id, name, email, password_hash, role, event_id, is_active) VALUES (1, 1, 'Assessoria', 'admin@local', ?, 'ADMIN', ?, 1)", (admin_hash, default_id))
        conn.execute("INSERT OR IGNORE INTO message_templates(event_id, name, content) VALUES (?, 'Confirmação RSVP', 'Olá {nome}, confirme sua presença no evento {evento}: {link}')", (default_id,))
        conn.execute("INSERT OR IGNORE INTO message_templates(event_id, name, content) VALUES (?, 'Mesa definida', 'Olá {nome}, sua mesa no evento {evento} é {mesa}.')", (default_id,))
    except sqlite3.OperationalError:
        pass
    _add_column_if_missing(conn, "automation_rules", "condition", "TEXT")
    _add_column_if_missing(conn, "background_jobs", "locked_at", "TEXT")
    _add_column_if_missing(conn, "background_jobs", "attempts", "INTEGER NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "background_jobs", "result_json", "TEXT")
    _add_column_if_missing(conn, "background_jobs", "max_retries", "INTEGER NOT NULL DEFAULT 3")
    _add_column_if_missing(conn, "background_jobs", "retry_count", "INTEGER NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "background_jobs", "priority", "INTEGER NOT NULL DEFAULT 100")
    _add_column_if_missing(conn, "background_jobs", "locked_by", "TEXT")
    _add_column_if_missing(conn, "background_jobs", "metadata_json", "TEXT")
    _add_column_if_missing(conn, "automation_rule_advanced", "schedule_type", "TEXT NOT NULL DEFAULT 'manual'")
    _add_column_if_missing(conn, "automation_rule_advanced", "interval_minutes", "INTEGER")
    _add_column_if_missing(conn, "automation_rule_advanced", "daily_time", "TEXT")
    _add_column_if_missing(conn, "automation_rule_advanced", "next_run_at", "TEXT")
    _add_column_if_missing(conn, "automation_rule_advanced", "last_run_at", "TEXT")
    _add_column_if_missing(conn, "automation_run_advanced", "error_message", "TEXT")
    _add_column_if_missing(conn, "automation_run_advanced", "affected_count", "INTEGER NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "audit_logs", "ip", "TEXT")
    _add_column_if_missing(conn, "audit_logs", "user_agent", "TEXT")
    _add_column_if_missing(conn, "audit_logs", "request_id", "TEXT")
    _add_column_if_missing(conn, "audit_logs", "severity", "TEXT NOT NULL DEFAULT 'info'")
    conn.execute("UPDATE messages SET status='pending' WHERE lower(status)='pendente'")
    conn.execute("UPDATE messages SET status='sent' WHERE lower(status)='enviado'")
    conn.execute("UPDATE messages SET status='error' WHERE lower(status)='erro'")
    conn.execute("UPDATE messages SET status='pending' WHERE status IS NULL OR status NOT IN ('pending','sent','error')")


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.executescript(PREMIUM_SCHEMA)
        conn.executescript(INTELLIGENCE_SCHEMA)
        conn.executescript(ADAPTIVE_SCHEMA)
        conn.executescript(COMPETITIVE_SCHEMA)
        conn.executescript(PORTAL_SCHEMA)
        conn.executescript(CRM_SCHEMA)
        conn.executescript(SAAS_PATCH_SCHEMA)
        conn.executescript(PRODUCTION_SAAS_SCHEMA)
        conn.executescript(SAAS_ADVANCED_SCHEMA)
        conn.executescript(PRODUCTION_CONSOLIDATION_SCHEMA)
        _migrate(conn)
        seed_tables(ensure_default_event(conn), conn)


def event_exists(event_id: int | None) -> bool:
    if not event_id:
        return False
    with connect() as conn:
        try:
            row = conn.execute("SELECT 1 FROM events WHERE id=?", (int(event_id),)).fetchone()
        except sqlite3.OperationalError:
            init_db()
            row = conn.execute("SELECT 1 FROM events WHERE id=?", (int(event_id),)).fetchone()
    return row is not None


def seed_tables(event_id: int, conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    if own:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
    assert conn is not None
    for i in range(1, 24):
        conn.execute("INSERT OR IGNORE INTO tables(event_id, name, capacity) VALUES(?, ?, ?)", (int(event_id), f"Mesa {i}", None))
    if own:
        conn.commit()
        conn.close()


# Eventos

def list_events() -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM events ORDER BY date IS NULL, date, id DESC").fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def create_event(name: str, date: str = "", location: str = "") -> int:
    init_db()
    with connect() as conn:
        cur = conn.execute("INSERT INTO events(name, date, location) VALUES (?, ?, ?)", (name.strip(), date, location.strip()))
        event_id = int(cur.lastrowid)
        seed_tables(event_id, conn)
    return event_id


def update_event(event_id: int, name: str, date: str = "", location: str = "") -> None:
    init_db()
    with connect() as conn:
        conn.execute("UPDATE events SET name=?, date=?, location=? WHERE id=?", (name.strip(), date, location.strip(), int(event_id)))


def get_event(event_id: int | None) -> dict:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM events WHERE id=?", (int(event_id),)).fetchone() if event_id else None
        if row is None:
            row = conn.execute("SELECT * FROM events ORDER BY id LIMIT 1").fetchone()
    return dict(row) if row else {"id": None, "name": "Sem evento"}


# Logs

def log_event(area: str, message: str, level: str = "INFO", detail: str | None = None, event_id: int | None = None) -> None:
    init_db()
    with connect() as conn:
        safe_id = _safe_event_id(event_id, conn)
        conn.execute(
            "INSERT INTO app_logs(event_id, area, level, message, detail) VALUES (?, ?, ?, ?, ?)",
            (safe_id, area, level.upper(), message, detail),
        )
        if level.upper() == "ERROR":
            conn.execute(
                "INSERT INTO error_logs(event_id, area, error_message, detail) VALUES (?, ?, ?, ?)",
                (safe_id, area, message, detail),
            )


# Mesas e grupos

def upsert_table(event_id: int, name: str, capacity: int | None = None, observation: str = "") -> None:
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        existing = conn.execute("SELECT id FROM tables WHERE event_id=? AND name=?", (event_id, name.strip())).fetchone()
        if existing:
            conn.execute("UPDATE tables SET capacity=?, observation=? WHERE id=? AND event_id=?", (capacity, observation, int(existing["id"]), event_id))
        else:
            conn.execute("INSERT INTO tables(event_id, name, capacity, observation) VALUES (?, ?, ?, ?)", (event_id, name.strip(), capacity, observation))


def delete_table(event_id: int, table_id: int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM tables WHERE id=? AND event_id=?", (int(table_id), int(event_id)))


def list_tables(event_id: int) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM tables WHERE event_id=? ORDER BY name", (int(event_id),)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def upsert_group(event_id: int, name: str, category: str = "", phone: str = "") -> None:
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        existing = conn.execute("SELECT id FROM groups WHERE event_id=? AND name=?", (event_id, name.strip())).fetchone()
        if existing:
            conn.execute("UPDATE groups SET category=?, phone=? WHERE id=? AND event_id=?", (category, phone, int(existing["id"]), event_id))
        else:
            conn.execute("INSERT INTO groups(event_id, name, category, phone) VALUES (?, ?, ?, ?)", (event_id, name.strip(), category, phone))


def delete_group(event_id: int, group_id: int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM groups WHERE id=? AND event_id=?", (int(group_id), int(event_id)))


def list_groups(event_id: int) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM groups WHERE event_id=? ORDER BY name", (int(event_id),)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


# Convidados

def create_guest(event_id: int, data: dict) -> int:
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        cur = conn.execute(
            """
            INSERT INTO guests(event_id, name, original_name, category, type, group_name, current_table, corrected_table, final_table, table_status, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                data.get("nome") or data.get("name") or data.get("nome_original") or "",
                data.get("nome_original") or data.get("original_name") or data.get("nome") or "",
                data.get("categoria") or data.get("category") or "",
                data.get("tipo") or data.get("type") or "",
                data.get("grupo") or data.get("group_name") or "",
                data.get("mesa_atual") or data.get("current_table") or "",
                data.get("mesa_corrigida") or data.get("corrected_table") or "",
                data.get("mesa_final") or data.get("final_table") or "",
                data.get("status_mesa") or data.get("table_status") or "",
                data.get("telefone") or data.get("phone") or "",
            ),
        )
        return int(cur.lastrowid)


def update_guest(event_id: int, guest_id: int, data: dict) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            UPDATE guests
            SET name=?, original_name=?, category=?, type=?, group_name=?, current_table=?, corrected_table=?, final_table=?, table_status=?, phone=?, updated_at=?
            WHERE id=? AND event_id=?
            """,
            (
                data.get("nome") or data.get("name") or "",
                data.get("nome_original") or data.get("original_name") or data.get("nome") or "",
                data.get("categoria") or data.get("category") or "",
                data.get("tipo") or data.get("type") or "",
                data.get("grupo") or data.get("group_name") or "",
                data.get("mesa_atual") or data.get("current_table") or "",
                data.get("mesa_corrigida") or data.get("corrected_table") or "",
                data.get("mesa_final") or data.get("final_table") or "",
                data.get("status_mesa") or data.get("table_status") or "",
                data.get("telefone") or data.get("phone") or "",
                _now(),
                int(guest_id),
                int(event_id),
            ),
        )


def delete_guest(event_id: int, guest_id: int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM guests WHERE id=? AND event_id=?", (int(guest_id), int(event_id)))


def replace_guests(df: pd.DataFrame, event_id: int) -> None:
    init_db()
    records = df.fillna("").to_dict(orient="records")
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        conn.execute("DELETE FROM guests WHERE event_id=?", (event_id,))
        conn.execute("DELETE FROM groups WHERE event_id=?", (event_id,))
        for row in records:
            conn.execute(
                """
                INSERT INTO guests(event_id, name, original_name, category, type, group_name, current_table, corrected_table, final_table, table_status, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    row.get("nome") or row.get("name") or row.get("nome_original") or "",
                    row.get("nome_original") or row.get("original_name") or row.get("nome") or "",
                    row.get("categoria") or row.get("category") or "",
                    row.get("tipo") or row.get("type") or "",
                    row.get("grupo") or row.get("group_name") or "",
                    row.get("mesa_atual") or row.get("current_table") or "",
                    row.get("mesa_corrigida") or row.get("corrected_table") or "",
                    row.get("mesa_final") or row.get("final_table") or "",
                    row.get("status_mesa") or row.get("table_status") or "",
                    row.get("telefone") or row.get("phone") or "",
                ),
            )
        if not df.empty:
            group_series = df.get("grupo", pd.Series(dtype=str)).fillna(df.get("nome_original", pd.Series(dtype=str)))
            for group_name, group_df in df.groupby(group_series):
                if not str(group_name).strip():
                    continue
                category = str(group_df["categoria"].dropna().iloc[0]) if "categoria" in group_df and not group_df["categoria"].dropna().empty else ""
                phone = str(group_df["telefone"].dropna().iloc[0]) if "telefone" in group_df and not group_df["telefone"].dropna().empty else ""
                conn.execute("INSERT OR IGNORE INTO groups(event_id, name, category, phone) VALUES (?, ?, ?, ?)", (event_id, str(group_name), category, phone))


def load_guests_df(event_id: int) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM guests WHERE event_id=? ORDER BY final_table, group_name, original_name", (int(event_id),)).fetchall()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([dict(r) for r in rows])
    return df.rename(columns={
        "name": "nome", "original_name": "nome_original", "category": "categoria", "type": "tipo",
        "group_name": "grupo", "current_table": "mesa_atual", "corrected_table": "mesa_corrigida",
        "final_table": "mesa_final", "table_status": "status_mesa", "phone": "telefone",
    })


# Importação

def create_import(event_id: int, source_file: str, total_records: int, status: str, detail: str = "") -> int:
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        cur = conn.execute(
            "INSERT INTO imports(event_id, source_file, total_records, status, detail) VALUES (?, ?, ?, ?, ?)",
            (event_id, source_file, total_records, status, detail),
        )
        import_id = int(cur.lastrowid)
        conn.execute("INSERT INTO import_logs(event_id, import_id, status, detail) VALUES (?, ?, ?, ?)", (event_id, import_id, status, detail))
        return import_id


# Mensagens

def enqueue_messages(event_id: int, items: Iterable[dict], skip_sent: bool = True) -> int:
    init_db()
    count = 0
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        for item in items:
            guest_id = item.get("guest_id")
            guest_id = int(guest_id) if str(guest_id or "").isdigit() else None
            phone = item.get("telefone", "")
            group_name = item.get("grupo", "")
            if skip_sent:
                if guest_id:
                    exists = conn.execute(
                        "SELECT 1 FROM messages WHERE event_id=? AND guest_id=? AND status='sent' LIMIT 1",
                        (event_id, guest_id),
                    ).fetchone()
                else:
                    exists = conn.execute(
                        "SELECT 1 FROM messages WHERE event_id=? AND status='sent' AND phone<>'' AND phone=? LIMIT 1",
                        (event_id, phone),
                    ).fetchone()
                if exists:
                    continue
            conn.execute(
                """
                INSERT INTO messages(event_id, guest_id, group_name, guest_name, phone, table_name, template, message_text, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                (event_id, guest_id, group_name, item.get("nome", ""), phone, item.get("mesa", ""), item.get("template", ""), item.get("mensagem", "")),
            )
            count += 1
    return count


def list_messages(event_id: int, status: str | None = None) -> pd.DataFrame:
    init_db()
    status = normalize_status(status)
    sql = "SELECT * FROM messages WHERE event_id=?"
    params: list = [int(event_id)]
    if status and status != "todos":
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def update_message_status(event_id: int, message_id: int, status: str, detail: str = "") -> None:
    init_db()
    status = normalize_status(status) or "pending"
    if status == "preview":
        return
    with connect() as conn:
        row = conn.execute("SELECT event_id FROM messages WHERE id=? AND event_id=?", (int(message_id), int(event_id))).fetchone()
        if row is None:
            raise ValueError("Mensagem não encontrada no evento ativo.")
        sent_at = _now() if status == "sent" else None
        conn.execute(
            "UPDATE messages SET status=?, error=CASE WHEN ?='error' THEN ? ELSE NULL END, sent_at=COALESCE(?, sent_at) WHERE id=? AND event_id=?",
            (status, status, detail, sent_at, int(message_id), int(event_id)),
        )
        guest_id = conn.execute("SELECT guest_id FROM messages WHERE id=? AND event_id=?", (int(message_id), int(event_id))).fetchone()
        retry_count = conn.execute("SELECT COUNT(*) AS c FROM message_logs WHERE message_id=? AND status='error'", (int(message_id),)).fetchone()
        conn.execute(
            "INSERT INTO message_logs(event_id, message_id, guest_id, status, detail, error_message, retries, sent_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (int(event_id), int(message_id), int(guest_id["guest_id"]) if guest_id and guest_id["guest_id"] else None, status, detail, detail if status == "error" else None, int(retry_count["c"] if retry_count else 0), sent_at),
        )


def read_logs(event_id: int, limit: int = 300) -> dict[str, pd.DataFrame]:
    init_db()
    with connect() as conn:
        app_logs = conn.execute("SELECT * FROM app_logs WHERE event_id=? ORDER BY created_at DESC LIMIT ?", (int(event_id), limit)).fetchall()
        msg_logs = conn.execute("SELECT * FROM message_logs WHERE event_id=? ORDER BY created_at DESC LIMIT ?", (int(event_id), limit)).fetchall()
        imports = conn.execute("SELECT * FROM imports WHERE event_id=? ORDER BY created_at DESC LIMIT ?", (int(event_id), limit)).fetchall()
        import_logs = conn.execute("SELECT * FROM import_logs WHERE event_id=? ORDER BY created_at DESC LIMIT ?", (int(event_id), limit)).fetchall()
        error_logs = conn.execute("SELECT * FROM error_logs WHERE event_id=? ORDER BY created_at DESC LIMIT ?", (int(event_id), limit)).fetchall()
        audit_logs = conn.execute("SELECT * FROM audit_logs WHERE event_id=? ORDER BY created_at DESC LIMIT ?", (int(event_id), limit)).fetchall()
    return {
        "app_logs": pd.DataFrame([dict(r) for r in app_logs]),
        "message_logs": pd.DataFrame([dict(r) for r in msg_logs]),
        "imports": pd.DataFrame([dict(r) for r in imports]),
        "import_logs": pd.DataFrame([dict(r) for r in import_logs]),
        "error_logs": pd.DataFrame([dict(r) for r in error_logs]),
        "audit_logs": pd.DataFrame([dict(r) for r in audit_logs]),
    }


# Premium ERP repositories
RSVP_STATUSES = {"pending", "confirmed", "declined", "maybe"}
RSVP_SOURCES = {"manual", "whatsapp", "import", "assessoria_vip"}
CHECKIN_METHODS = {"manual", "qr_code", "import"}
TASK_STATUSES = {"pending", "in_progress", "done", "canceled"}
TASK_PRIORITIES = {"low", "medium", "high", "critical"}
TIMELINE_STATUSES = {"planned", "running", "done", "delayed"}


def audit_log(event_id: int, entity_type: str, entity_id: int | None, action: str, details: str = "") -> None:
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        conn.execute(
            "INSERT INTO audit_logs(event_id, entity_type, entity_id, action, details) VALUES (?, ?, ?, ?, ?)",
            (event_id, entity_type, entity_id, action, details),
        )


def get_rsvp(event_id: int, status: str | None = None) -> pd.DataFrame:
    init_db()
    sql = """
        SELECT g.id AS guest_id, g.original_name AS guest_name, g.name, g.group_name, g.final_table, g.phone,
               COALESCE(r.id, 0) AS rsvp_id,
               COALESCE(r.status, 'pending') AS status,
               COALESCE(r.source, 'manual') AS source,
               COALESCE(r.notes, '') AS notes,
               r.updated_at, r.created_at
        FROM guests g
        LEFT JOIN guest_rsvp r ON r.event_id = g.event_id AND r.guest_id = g.id
        WHERE g.event_id=?
    """
    params: list = [int(event_id)]
    if status and status != "todos":
        sql += " AND COALESCE(r.status, 'pending')=?"
        params.append(status)
    sql += " ORDER BY status, g.group_name, g.original_name"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def upsert_rsvp(event_id: int, guest_id: int, status: str, source: str = "manual", notes: str = "") -> None:
    if status not in RSVP_STATUSES:
        raise ValueError("Status de RSVP inválido.")
    if source not in RSVP_SOURCES:
        raise ValueError("Origem de RSVP inválida.")
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT id FROM guests WHERE id=? AND event_id=?", (int(guest_id), int(event_id))).fetchone()
        if not row:
            raise ValueError("Convidado não pertence ao evento ativo.")
        conn.execute(
            """
            INSERT INTO guest_rsvp(event_id, guest_id, status, source, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id, guest_id) DO UPDATE SET
                status=excluded.status, source=excluded.source, notes=excluded.notes, updated_at=excluded.updated_at
            """,
            (int(event_id), int(guest_id), status, source, notes, _now()),
        )
    audit_log(event_id, "guest_rsvp", guest_id, "upsert", f"status={status}; source={source}; notes={notes}")


def get_checkins(event_id: int, checked: str | None = None) -> pd.DataFrame:
    init_db()
    sql = """
        SELECT g.id AS guest_id, g.original_name AS guest_name, g.name, g.group_name, g.final_table, g.phone,
               COALESCE(c.id, 0) AS checkin_id,
               COALESCE(c.checked_in, 0) AS checked_in,
               c.checked_in_at,
               COALESCE(c.method, 'manual') AS method,
               COALESCE(c.notes, '') AS notes
        FROM guests g
        LEFT JOIN guest_checkins c ON c.event_id = g.event_id AND c.guest_id = g.id
        WHERE g.event_id=?
    """
    params: list = [int(event_id)]
    if checked == "presentes":
        sql += " AND COALESCE(c.checked_in, 0)=1"
    elif checked == "ausentes":
        sql += " AND COALESCE(c.checked_in, 0)=0"
    sql += " ORDER BY checked_in DESC, g.group_name, g.original_name"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def set_checkin(event_id: int, guest_id: int, checked_in: bool, method: str = "manual", notes: str = "") -> None:
    if method not in CHECKIN_METHODS:
        raise ValueError("Método de check-in inválido.")
    init_db()
    checked = 1 if checked_in else 0
    checked_at = _now() if checked_in else None
    with connect() as conn:
        row = conn.execute("SELECT id FROM guests WHERE id=? AND event_id=?", (int(guest_id), int(event_id))).fetchone()
        if not row:
            raise ValueError("Convidado não pertence ao evento ativo.")
        conn.execute(
            """
            INSERT INTO guest_checkins(event_id, guest_id, checked_in, checked_in_at, method, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id, guest_id) DO UPDATE SET
                checked_in=excluded.checked_in, checked_in_at=excluded.checked_in_at, method=excluded.method, notes=excluded.notes
            """,
            (int(event_id), int(guest_id), checked, checked_at, method, notes),
        )
    audit_log(event_id, "guest_checkin", guest_id, "checkin" if checked_in else "undo_checkin", notes)


def list_tasks(event_id: int, status: str | None = None, priority: str | None = None) -> pd.DataFrame:
    init_db()
    sql = "SELECT * FROM event_tasks WHERE event_id=?"
    params: list = [int(event_id)]
    if status and status != "todos":
        sql += " AND status=?"
        params.append(status)
    if priority and priority != "todas":
        sql += " AND priority=?"
        params.append(priority)
    sql += " ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, due_date IS NULL, due_date, id DESC"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def create_task(event_id: int, title: str, description: str = "", status: str = "pending", priority: str = "medium", due_date: str = "", owner: str = "") -> int:
    if status not in TASK_STATUSES or priority not in TASK_PRIORITIES:
        raise ValueError("Status ou prioridade inválidos.")
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO event_tasks(event_id, title, description, status, priority, due_date, owner) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (int(event_id), title.strip(), description, status, priority, due_date, owner),
        )
        task_id = int(cur.lastrowid)
    audit_log(event_id, "event_task", task_id, "create", title)
    return task_id


def update_task(event_id: int, task_id: int, **fields) -> None:
    allowed = {"title", "description", "status", "priority", "due_date", "owner"}
    data = {k: v for k, v in fields.items() if k in allowed}
    if not data:
        return
    if data.get("status") and data["status"] not in TASK_STATUSES:
        raise ValueError("Status de tarefa inválido.")
    if data.get("priority") and data["priority"] not in TASK_PRIORITIES:
        raise ValueError("Prioridade inválida.")
    data["updated_at"] = _now()
    sets = ", ".join([f"{k}=?" for k in data])
    params = list(data.values()) + [int(task_id), int(event_id)]
    init_db()
    with connect() as conn:
        conn.execute(f"UPDATE event_tasks SET {sets} WHERE id=? AND event_id=?", tuple(params))
    audit_log(event_id, "event_task", task_id, "update", str(data))


def delete_task(event_id: int, task_id: int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM event_tasks WHERE id=? AND event_id=?", (int(task_id), int(event_id)))
    audit_log(event_id, "event_task", task_id, "delete", "")


def list_timeline(event_id: int, status: str | None = None) -> pd.DataFrame:
    init_db()
    sql = "SELECT * FROM event_timeline_items WHERE event_id=?"
    params: list = [int(event_id)]
    if status and status != "todos":
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY time, id"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def create_timeline_item(event_id: int, time: str, title: str, description: str = "", owner: str = "", status: str = "planned") -> int:
    if status not in TIMELINE_STATUSES:
        raise ValueError("Status de cronograma inválido.")
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO event_timeline_items(event_id, time, title, description, owner, status) VALUES (?, ?, ?, ?, ?, ?)",
            (int(event_id), time, title.strip(), description, owner, status),
        )
        item_id = int(cur.lastrowid)
    audit_log(event_id, "event_timeline_item", item_id, "create", title)
    return item_id


def update_timeline_item(event_id: int, item_id: int, **fields) -> None:
    allowed = {"time", "title", "description", "owner", "status"}
    data = {k: v for k, v in fields.items() if k in allowed}
    if not data:
        return
    if data.get("status") and data["status"] not in TIMELINE_STATUSES:
        raise ValueError("Status de cronograma inválido.")
    data["updated_at"] = _now()
    sets = ", ".join([f"{k}=?" for k in data])
    params = list(data.values()) + [int(item_id), int(event_id)]
    init_db()
    with connect() as conn:
        conn.execute(f"UPDATE event_timeline_items SET {sets} WHERE id=? AND event_id=?", tuple(params))
    audit_log(event_id, "event_timeline_item", item_id, "update", str(data))


def delete_timeline_item(event_id: int, item_id: int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM event_timeline_items WHERE id=? AND event_id=?", (int(item_id), int(event_id)))
    audit_log(event_id, "event_timeline_item", item_id, "delete", "")


def count_critical_table_conflicts(event_id: int) -> int:
    from services.table_validation_service import validate_tables
    return sum(1 for item in validate_tables(event_id) if item.get("severity") == "critical")


def update_guest_table(event_id: int, guest_id: int, table_name: str, status: str = "sugerida") -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            "UPDATE guests SET final_table=?, table_status=?, updated_at=? WHERE id=? AND event_id=?",
            (table_name, status, _now(), int(guest_id), int(event_id)),
        )
    audit_log(event_id, "guest", guest_id, "update_table", f"mesa={table_name}; status={status}")


# Intelligence repositories
AUTOMATION_TRIGGERS = {"RSVP_confirmed", "RSVP_pending", "event_minus_3_days", "event_minus_1_day", "checkin_missing"}
AUTOMATION_ACTIONS = {"send_message", "reminder", "create_task"}


def upsert_guest_score(event_id: int, guest_id: int, attendance_probability: float, priority_score: float, engagement_score: float, explanation: str = "") -> None:
    init_db()
    attendance_probability = max(0.0, min(1.0, float(attendance_probability)))
    priority_score = max(0.0, min(100.0, float(priority_score)))
    engagement_score = max(0.0, min(100.0, float(engagement_score)))
    with connect() as conn:
        row = conn.execute("SELECT id FROM guests WHERE id=? AND event_id=?", (int(guest_id), int(event_id))).fetchone()
        if not row:
            raise ValueError("Convidado não pertence ao evento ativo.")
        conn.execute(
            """
            INSERT INTO guest_score(event_id, guest_id, attendance_probability, priority_score, engagement_score, explanation, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id, guest_id) DO UPDATE SET
                attendance_probability=excluded.attendance_probability,
                priority_score=excluded.priority_score,
                engagement_score=excluded.engagement_score,
                explanation=excluded.explanation,
                updated_at=excluded.updated_at
            """,
            (int(event_id), int(guest_id), attendance_probability, priority_score, engagement_score, explanation, _now()),
        )


def list_guest_scores(event_id: int) -> pd.DataFrame:
    init_db()
    sql = """
        SELECT g.id AS guest_id, g.original_name AS guest_name, g.group_name, g.final_table, g.phone,
               COALESCE(r.status, 'pending') AS rsvp_status,
               COALESCE(c.checked_in, 0) AS checked_in,
               COALESCE(s.attendance_probability, 0) AS attendance_probability,
               COALESCE(s.priority_score, 0) AS priority_score,
               COALESCE(s.engagement_score, 0) AS engagement_score,
               COALESCE(s.explanation, '') AS explanation,
               s.updated_at
        FROM guests g
        LEFT JOIN guest_rsvp r ON r.event_id=g.event_id AND r.guest_id=g.id
        LEFT JOIN guest_checkins c ON c.event_id=g.event_id AND c.guest_id=g.id
        LEFT JOIN guest_score s ON s.event_id=g.event_id AND s.guest_id=g.id
        WHERE g.event_id=?
        ORDER BY priority_score DESC, attendance_probability DESC, g.original_name
    """
    with connect() as conn:
        rows = conn.execute(sql, (int(event_id),)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def create_automation_rule(event_id: int, name: str, trigger: str, action: str, template: str = "", target_status: str = "", enabled: bool = True, condition: str = "") -> int:
    if trigger not in AUTOMATION_TRIGGERS:
        raise ValueError("Trigger de automação inválido.")
    if action not in AUTOMATION_ACTIONS:
        raise ValueError("Ação de automação inválida.")
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO automation_rules(event_id, name, trigger, action, condition, enabled, template, target_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (int(event_id), name.strip(), trigger, action, condition, 1 if enabled else 0, template, target_status),
        )
        rule_id = int(cur.lastrowid)
    audit_log(event_id, "automation_rule", rule_id, "create", f"trigger={trigger}; action={action}")
    return rule_id


def update_automation_rule(event_id: int, rule_id: int, **fields) -> None:
    allowed = {"name", "trigger", "action", "condition", "enabled", "template", "target_status"}
    data = {k: v for k, v in fields.items() if k in allowed}
    if not data:
        return
    if "trigger" in data and data["trigger"] not in AUTOMATION_TRIGGERS:
        raise ValueError("Trigger de automação inválido.")
    if "action" in data and data["action"] not in AUTOMATION_ACTIONS:
        raise ValueError("Ação de automação inválida.")
    if "enabled" in data:
        data["enabled"] = 1 if bool(data["enabled"]) else 0
    data["updated_at"] = _now()
    sets = ", ".join([f"{k}=?" for k in data])
    params = list(data.values()) + [int(rule_id), int(event_id)]
    init_db()
    with connect() as conn:
        conn.execute(f"UPDATE automation_rules SET {sets} WHERE id=? AND event_id=?", tuple(params))
    audit_log(event_id, "automation_rule", rule_id, "update", str(data))


def delete_automation_rule(event_id: int, rule_id: int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM automation_rules WHERE id=? AND event_id=?", (int(rule_id), int(event_id)))
    audit_log(event_id, "automation_rule", rule_id, "delete", "")


def list_automation_rules(event_id: int, enabled_only: bool = False) -> pd.DataFrame:
    init_db()
    sql = "SELECT * FROM automation_rules WHERE event_id=?"
    params: list = [int(event_id)]
    if enabled_only:
        sql += " AND enabled=1"
    sql += " ORDER BY enabled DESC, trigger, id DESC"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def record_automation_run(event_id: int, rule_id: int | None, status: str, processed_count: int = 0, details: str = "") -> int:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO automation_runs(event_id, rule_id, status, processed_count, details) VALUES (?, ?, ?, ?, ?)",
            (int(event_id), int(rule_id) if rule_id else None, status, int(processed_count), details),
        )
        run_id = int(cur.lastrowid)
        if rule_id:
            conn.execute("UPDATE automation_rules SET last_run_at=?, updated_at=? WHERE id=? AND event_id=?", (_now(), _now(), int(rule_id), int(event_id)))
    return run_id


def list_automation_runs(event_id: int, limit: int = 100) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT ar.*, r.name AS rule_name, r.trigger, r.action
            FROM automation_runs ar
            LEFT JOIN automation_rules r ON r.id=ar.rule_id AND r.event_id=ar.event_id
            WHERE ar.event_id=?
            ORDER BY ar.created_at DESC
            LIMIT ?
            """,
            (int(event_id), int(limit)),
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def get_live_dashboard_data(event_id: int) -> dict:
    guests = load_guests_df(event_id)
    checkins = get_checkins(event_id)
    messages_sent = list_messages(event_id, "sent")
    rsvp = get_rsvp(event_id)
    tables_df = list_tables(event_id)
    total = len(guests)
    present = int(checkins["checked_in"].fillna(0).astype(int).sum()) if not checkins.empty else 0
    confirmed = int((rsvp["status"] == "confirmed").sum()) if not rsvp.empty else 0
    missing = checkins[checkins["checked_in"].fillna(0).astype(int) == 0] if not checkins.empty else pd.DataFrame()
    table_status = pd.DataFrame()
    if not guests.empty:
        occupied = guests[guests["mesa_final"].fillna("").astype(str).ne("")].groupby("mesa_final").size().reset_index(name="occupied")
        if not tables_df.empty:
            table_status = tables_df.merge(occupied, how="left", left_on="name", right_on="mesa_final")
            table_status["occupied"] = table_status["occupied"].fillna(0).astype(int)
            table_status["capacity"] = table_status["capacity"].fillna(0).astype(int)
            table_status["available"] = table_status["capacity"] - table_status["occupied"]
    return {
        "total_guests": total,
        "present": present,
        "presence_rate": (present / total) if total else 0,
        "confirmed": confirmed,
        "sent_messages": 0 if messages_sent.empty else len(messages_sent),
        "missing_guests": missing,
        "table_status": table_status,
    }


# Adaptive intelligence repositories
def upsert_adaptive_weight(event_id: int, weight_name: str, weight_value: float, evidence_count: int = 0) -> None:
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        conn.execute(
            """
            INSERT INTO adaptive_weights(event_id, weight_name, weight_value, evidence_count, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(event_id, weight_name) DO UPDATE SET
                weight_value=excluded.weight_value,
                evidence_count=adaptive_weights.evidence_count + excluded.evidence_count,
                updated_at=excluded.updated_at
            """,
            (event_id, weight_name, float(weight_value), int(evidence_count), _now()),
        )


def list_adaptive_weights(event_id: int) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM adaptive_weights WHERE event_id=? ORDER BY weight_name", (int(event_id),)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def upsert_event_profile(event_id: int, profile: dict) -> None:
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        conn.execute(
            """
            INSERT INTO event_profiles(event_id, confirmation_rate, presence_rate, no_show_rate, avg_attendance_probability, dominant_groups, operational_risk, learned_notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                confirmation_rate=excluded.confirmation_rate,
                presence_rate=excluded.presence_rate,
                no_show_rate=excluded.no_show_rate,
                avg_attendance_probability=excluded.avg_attendance_probability,
                dominant_groups=excluded.dominant_groups,
                operational_risk=excluded.operational_risk,
                learned_notes=excluded.learned_notes,
                updated_at=excluded.updated_at
            """,
            (
                event_id,
                float(profile.get("confirmation_rate", 0)),
                float(profile.get("presence_rate", 0)),
                float(profile.get("no_show_rate", 0)),
                float(profile.get("avg_attendance_probability", 0)),
                str(profile.get("dominant_groups", "")),
                str(profile.get("operational_risk", "low")),
                str(profile.get("learned_notes", "")),
                _now(),
            ),
        )


def get_event_profile(event_id: int) -> dict:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM event_profiles WHERE event_id=?", (int(event_id),)).fetchone()
    return dict(row) if row else {}


def create_intelligent_insight(event_id: int, severity: str, title: str, message: str, action_suggestion: str = "") -> int:
    if severity not in {"info", "warning", "critical"}:
        severity = "info"
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        cur = conn.execute(
            "INSERT INTO intelligent_insights(event_id, severity, title, message, action_suggestion) VALUES (?, ?, ?, ?, ?)",
            (event_id, severity, title, message, action_suggestion),
        )
        insight_id = int(cur.lastrowid)
    audit_log(event_id, "intelligent_insight", insight_id, "create", f"{severity}: {title}")
    return insight_id


def list_intelligent_insights(event_id: int, limit: int = 50) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM intelligent_insights WHERE event_id=? ORDER BY created_at DESC LIMIT ?",
            (int(event_id), int(limit)),
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def record_orchestrator_decision(event_id: int, decision_type: str, status: str, summary: str, details: str = "") -> int:
    if status not in {"executed", "skipped", "error", "dry_run"}:
        status = "executed"
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        cur = conn.execute(
            "INSERT INTO orchestrator_decisions(event_id, decision_type, status, summary, details) VALUES (?, ?, ?, ?, ?)",
            (event_id, decision_type, status, summary, details),
        )
        decision_id = int(cur.lastrowid)
    audit_log(event_id, "orchestrator", decision_id, status, summary)
    return decision_id


def list_orchestrator_decisions(event_id: int, limit: int = 100) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM orchestrator_decisions WHERE event_id=? ORDER BY created_at DESC LIMIT ?",
            (int(event_id), int(limit)),
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


# Competitive intelligence repositories
def upsert_global_event_insight(event_id: int, metrics: dict, snapshot_json: str = "", source: str = "adaptive_engine") -> None:
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        event = conn.execute("SELECT name, date, location FROM events WHERE id=?", (event_id,)).fetchone()
        conn.execute(
            """
            INSERT INTO global_event_insights(
                event_id, event_name, event_date, location, total_guests, confirmation_rate,
                presence_rate, no_show_rate, table_efficiency, avg_attendance_probability,
                critical_conflicts, source, snapshot_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                event_name=excluded.event_name,
                event_date=excluded.event_date,
                location=excluded.location,
                total_guests=excluded.total_guests,
                confirmation_rate=excluded.confirmation_rate,
                presence_rate=excluded.presence_rate,
                no_show_rate=excluded.no_show_rate,
                table_efficiency=excluded.table_efficiency,
                avg_attendance_probability=excluded.avg_attendance_probability,
                critical_conflicts=excluded.critical_conflicts,
                source=excluded.source,
                snapshot_json=excluded.snapshot_json,
                updated_at=excluded.updated_at
            """,
            (
                event_id,
                event["name"] if event else "",
                event["date"] if event else "",
                event["location"] if event else "",
                int(metrics.get("total_guests", 0) or 0),
                float(metrics.get("confirmation_rate", 0) or 0),
                float(metrics.get("presence_rate", 0) or 0),
                float(metrics.get("no_show_rate", 0) or 0),
                float(metrics.get("table_efficiency", 0) or 0),
                float(metrics.get("avg_attendance_probability", 0) or 0),
                int(metrics.get("critical_conflicts", 0) or 0),
                source,
                snapshot_json,
                _now(),
            ),
        )
    audit_log(event_id, "global_event_insight", event_id, "upsert", f"source={source}")


def list_global_event_insights(exclude_event_id: int | None = None, limit: int = 200) -> pd.DataFrame:
    init_db()
    sql = "SELECT * FROM global_event_insights"
    params: list = []
    if exclude_event_id:
        sql += " WHERE event_id<>?"
        params.append(int(exclude_event_id))
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(int(limit))
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def upsert_guest_profile(event_id: int, guest_id: int, behavioral_type: str, attendance_pattern: str, influence_score: float, profile_notes: str = "") -> None:
    valid_types = {"champion", "reliable", "needs_followup", "at_risk", "declined", "unknown"}
    valid_patterns = {"always_present", "confirmed_present", "confirmed_absent", "uncertain", "declined", "unknown"}
    if behavioral_type not in valid_types:
        behavioral_type = "unknown"
    if attendance_pattern not in valid_patterns:
        attendance_pattern = "unknown"
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT id FROM guests WHERE id=? AND event_id=?", (int(guest_id), int(event_id))).fetchone()
        if not row:
            raise ValueError("Convidado não pertence ao evento ativo.")
        conn.execute(
            """
            INSERT INTO guest_profile(event_id, guest_id, behavioral_type, attendance_pattern, influence_score, profile_notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id, guest_id) DO UPDATE SET
                behavioral_type=excluded.behavioral_type,
                attendance_pattern=excluded.attendance_pattern,
                influence_score=excluded.influence_score,
                profile_notes=excluded.profile_notes,
                updated_at=excluded.updated_at
            """,
            (int(event_id), int(guest_id), behavioral_type, attendance_pattern, max(0, min(100, float(influence_score))), profile_notes, _now()),
        )


def list_guest_profiles(event_id: int) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT p.*, g.original_name AS guest_name, g.group_name, g.final_table, g.phone
            FROM guest_profile p
            JOIN guests g ON g.id=p.guest_id AND g.event_id=p.event_id
            WHERE p.event_id=?
            ORDER BY p.influence_score DESC, g.group_name, g.original_name
            """,
            (int(event_id),),
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def create_proactive_action(event_id: int, action_type: str, priority: str, title: str, description: str = "", payload_json: str = "") -> int:
    if priority not in {"low", "medium", "high", "critical"}:
        priority = "medium"
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        existing = conn.execute(
            "SELECT id FROM proactive_actions WHERE event_id=? AND status='suggested' AND action_type=? AND title=? LIMIT 1",
            (event_id, action_type, title),
        ).fetchone()
        if existing:
            return int(existing["id"])
        cur = conn.execute(
            "INSERT INTO proactive_actions(event_id, action_type, priority, title, description, payload_json) VALUES (?, ?, ?, ?, ?, ?)",
            (event_id, action_type, priority, title, description, payload_json),
        )
        action_id = int(cur.lastrowid)
    audit_log(event_id, "proactive_action", action_id, "suggest", f"{priority}: {title}")
    return action_id


def update_proactive_action_status(event_id: int, action_id: int, status: str) -> None:
    if status not in {"suggested", "accepted", "dismissed", "done"}:
        raise ValueError("Status de ação proativa inválido.")
    init_db()
    with connect() as conn:
        conn.execute("UPDATE proactive_actions SET status=?, updated_at=? WHERE id=? AND event_id=?", (status, _now(), int(action_id), int(event_id)))
    audit_log(event_id, "proactive_action", action_id, "status_update", status)


def list_proactive_actions(event_id: int, status: str | None = None) -> pd.DataFrame:
    init_db()
    sql = "SELECT * FROM proactive_actions WHERE event_id=?"
    params: list = [int(event_id)]
    if status and status != "todos":
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, created_at DESC"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


# Portal do Convidado repositories

def ensure_guest_public_link(event_id: int, guest_id: int, token: str, expires_at: str | None = None) -> int:
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        guest = conn.execute("SELECT id FROM guests WHERE id=? AND event_id=?", (int(guest_id), event_id)).fetchone()
        if not guest:
            raise ValueError("Convidado não pertence ao evento ativo.")
        existing = conn.execute("SELECT id FROM guest_public_links WHERE event_id=? AND guest_id=?", (event_id, int(guest_id))).fetchone()
        if existing:
            conn.execute(
                "UPDATE guest_public_links SET token=?, expires_at=COALESCE(?, expires_at) WHERE id=? AND event_id=?",
                (token, expires_at, int(existing["id"]), event_id),
            )
            link_id = int(existing["id"])
        else:
            cur = conn.execute(
                "INSERT INTO guest_public_links(event_id, guest_id, token, expires_at) VALUES (?, ?, ?, ?)",
                (event_id, int(guest_id), token, expires_at),
            )
            link_id = int(cur.lastrowid)
    audit_log(event_id, "guest_public_link", guest_id, "upsert", "Link público gerado/atualizado")
    return link_id


def get_guest_public_link_by_token(token: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT l.*, e.tenant_id, e.name AS event_name, e.date AS event_date, e.location AS event_location,
                   g.original_name AS guest_name, g.name, g.group_name, g.final_table, g.phone AS guest_phone,
                   g.invitation_type, g.invitation_label, g.category
            FROM guest_public_links l
            JOIN events e ON e.id = l.event_id
            JOIN guests g ON g.id = l.guest_id AND g.event_id = l.event_id
            WHERE l.token=?
            """,
            (token,),
        ).fetchone()
    return dict(row) if row else None


def mark_guest_public_link_used(event_id: int, link_id: int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("UPDATE guest_public_links SET used_at=? WHERE id=? AND event_id=?", (_now(), int(link_id), int(event_id)))


def upsert_guest_portal_response(event_id: int, guest_id: int, link_id: int | None, data: dict) -> None:
    status = str(data.get("confirm_presence") or "pending").strip().lower()
    if status not in RSVP_STATUSES:
        status = "pending"
    needs_bus = 1 if str(data.get("needs_bus") or "").lower() in {"1", "true", "on", "yes", "sim"} else 0
    try:
        companions_count = max(0, int(data.get("companions_count") or 0))
    except ValueError:
        companions_count = 0
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        guest = conn.execute("SELECT id FROM guests WHERE id=? AND event_id=?", (int(guest_id), event_id)).fetchone()
        if not guest:
            raise ValueError("Convidado não pertence ao evento informado.")
        conn.execute(
            """
            INSERT INTO guest_portal_responses(
                event_id, guest_id, link_id, confirm_presence, needs_bus, bus_pickup_point,
                companions_count, dietary_restrictions, notes, phone, submitted_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id, guest_id) DO UPDATE SET
                link_id=excluded.link_id,
                confirm_presence=excluded.confirm_presence,
                needs_bus=excluded.needs_bus,
                bus_pickup_point=excluded.bus_pickup_point,
                companions_count=excluded.companions_count,
                dietary_restrictions=excluded.dietary_restrictions,
                notes=excluded.notes,
                phone=excluded.phone,
                updated_at=excluded.updated_at
            """,
            (
                event_id,
                int(guest_id),
                int(link_id) if link_id else None,
                status,
                needs_bus,
                str(data.get("bus_pickup_point") or "").strip(),
                companions_count,
                str(data.get("dietary_restrictions") or "").strip(),
                str(data.get("notes") or "").strip(),
                str(data.get("phone") or "").strip(),
                _now(),
                _now(),
            ),
        )
        if str(data.get("phone") or "").strip():
            conn.execute("UPDATE guests SET phone=?, updated_at=? WHERE id=? AND event_id=?", (str(data.get("phone")).strip(), _now(), int(guest_id), event_id))
    upsert_rsvp(event_id, guest_id, status, source="whatsapp", notes=str(data.get("notes") or ""))
    if link_id:
        mark_guest_public_link_used(event_id, link_id)
    audit_log(event_id, "guest_portal_response", guest_id, "submit", f"status={status}; needs_bus={needs_bus}; companions={companions_count}")


def list_guest_public_links(event_id: int) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT l.*, g.original_name AS guest_name, g.group_name, g.final_table, g.phone,
                   r.confirm_presence, r.needs_bus, r.bus_pickup_point, r.companions_count,
                   r.dietary_restrictions, r.notes, r.submitted_at
            FROM guest_public_links l
            JOIN guests g ON g.id = l.guest_id AND g.event_id = l.event_id
            LEFT JOIN guest_portal_responses r ON r.event_id = l.event_id AND r.guest_id = l.guest_id
            WHERE l.event_id=?
            ORDER BY g.group_name, g.original_name
            """,
            (int(event_id),),
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def list_guest_portal_responses(event_id: int, only_bus: bool = False) -> pd.DataFrame:
    init_db()
    sql = """
        SELECT r.*, g.original_name AS guest_name, g.group_name, g.final_table
        FROM guest_portal_responses r
        JOIN guests g ON g.id = r.guest_id AND g.event_id = r.event_id
        WHERE r.event_id=?
    """
    params: list = [int(event_id)]
    if only_bus:
        sql += " AND r.needs_bus=1"
    sql += " ORDER BY r.updated_at DESC"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def event_is_closed(event_id: int) -> bool:
    from datetime import date as _date, datetime as _datetime
    event = get_event(event_id)
    raw = str(event.get("date") or "").strip()
    if not raw:
        return False
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return _datetime.strptime(raw[:10], fmt).date() < _date.today()
        except ValueError:
            continue
    return False


# CRM / Central de Contatos
CONTACT_SOURCES = {"manual", "excel", "csv", "vcf", "pdf", "portal"}
CAMPAIGN_STATUSES = {"draft", "queued", "running", "done", "partial_error", "error", "canceled"}
RECIPIENT_STATUSES = {"pending", "sent", "error", "skipped"}


def upsert_contact(event_id: int, data: dict) -> int:
    init_db()
    source = (data.get("source") or "manual").strip().lower()
    if source not in CONTACT_SOURCES:
        source = "manual"
    phone = str(data.get("phone") or "").strip()
    if not phone:
        raise ValueError("Telefone é obrigatório para contato.")
    name = str(data.get("name") or "").strip() or phone
    guest_id = data.get("guest_id")
    guest_id = int(guest_id) if str(guest_id or "").isdigit() else None
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        if guest_id:
            row = conn.execute("SELECT id FROM guests WHERE id=? AND event_id=?", (guest_id, event_id)).fetchone()
            if not row:
                guest_id = None
        existing = conn.execute("SELECT id FROM event_contacts WHERE event_id=? AND phone=?", (event_id, phone)).fetchone()
        payload = (
            event_id, guest_id, name, phone, data.get("email", ""), data.get("group_name", ""), source,
            data.get("tags", ""), data.get("notes", ""), 1 if data.get("is_valid", True) else 0, _now()
        )
        if existing:
            contact_id = int(existing["id"])
            conn.execute(
                """
                UPDATE event_contacts
                SET guest_id=COALESCE(?, guest_id), name=?, email=?, group_name=?, source=?, tags=?, notes=?, is_valid=?, updated_at=?
                WHERE id=? AND event_id=?
                """,
                (guest_id, name, data.get("email", ""), data.get("group_name", ""), source, data.get("tags", ""), data.get("notes", ""), 1 if data.get("is_valid", True) else 0, _now(), contact_id, event_id),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO event_contacts(event_id, guest_id, name, phone, email, group_name, source, tags, notes, is_valid, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            contact_id = int(cur.lastrowid)
    audit_log(event_id, "event_contact", contact_id, "upsert", f"source={source}; phone={phone}")
    return contact_id


def bulk_upsert_contacts(event_id: int, contacts: list[dict], source: str = "manual") -> dict:
    created_or_updated = 0
    invalid = 0
    skipped = 0
    for item in contacts:
        item = dict(item)
        item["source"] = item.get("source") or source
        if not str(item.get("phone") or "").strip():
            invalid += 1
            continue
        try:
            upsert_contact(event_id, item)
            created_or_updated += 1
        except Exception:
            skipped += 1
    log_event("contacts", "Importação de contatos processada", detail=f"ok={created_or_updated}; invalid={invalid}; skipped={skipped}; source={source}", event_id=event_id)
    return {"created_or_updated": created_or_updated, "invalid": invalid, "skipped": skipped}


def record_contact_import_log(event_id: int, source: str, result: dict) -> None:
    """Registra resumo amigável da importação de contatos no log interno."""
    init_db()
    total = int(result.get("total") or 0)
    imported = int(result.get("created_or_updated") or result.get("imported") or 0)
    invalid = int(result.get("invalid") or 0)
    duplicates = int(result.get("duplicates") or 0)
    skipped = int(result.get("skipped") or 0) + int(result.get("duplicates_ignored") or 0)
    status = "success" if imported and not invalid else ("partial" if imported else "warning")
    detail = (
        f"Importação de contatos ({source}): {imported} salvos, "
        f"{invalid} inválidos, {duplicates} duplicados, {skipped} ignorados."
    )
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO import_logs(
                event_id, source, total_records, imported_count, invalid_count,
                duplicate_count, skipped_count, status, detail
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (int(event_id), source, total, imported, invalid, duplicates, skipped, status, detail),
        )
    log_event("contacts_import", detail, event_id=event_id)


def list_contacts(event_id: int, group_name: str | None = None, tag: str | None = None, valid: str | None = None) -> pd.DataFrame:
    init_db()
    sql = "SELECT * FROM event_contacts WHERE event_id=?"
    params: list = [int(event_id)]
    if group_name and group_name != "Todos":
        sql += " AND COALESCE(group_name,'')=?"
        params.append(group_name)
    if tag:
        sql += " AND COALESCE(tags,'') LIKE ?"
        params.append(f"%{tag}%")
    if valid == "válidos":
        sql += " AND is_valid=1"
    elif valid == "inválidos":
        sql += " AND is_valid=0"
    sql += " ORDER BY group_name, name"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def delete_contact(event_id: int, contact_id: int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM event_contacts WHERE id=? AND event_id=?", (int(contact_id), int(event_id)))
    audit_log(event_id, "event_contact", contact_id, "delete", "")


def sync_contacts_from_guests(event_id: int) -> dict:
    df = load_guests_df(event_id)
    contacts = []
    for _, row in df.fillna("").iterrows():
        phone = str(row.get("telefone", "")).strip()
        if not phone:
            continue
        contacts.append({
            "guest_id": int(row.get("id")) if str(row.get("id", "")).isdigit() else None,
            "name": row.get("nome_original") or row.get("nome") or "",
            "phone": phone,
            "group_name": row.get("grupo", ""),
            "source": "pdf",
            "notes": "Sincronizado a partir dos convidados do evento.",
        })
    return bulk_upsert_contacts(event_id, contacts, source="pdf")


def create_campaign(event_id: int, name: str, template: str, contact_ids: list[int]) -> int:
    init_db()
    if not contact_ids:
        raise ValueError("Selecione pelo menos um contato.")
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        cur = conn.execute(
            "INSERT INTO whatsapp_campaigns(event_id, name, template, status, updated_at) VALUES (?, ?, ?, 'queued', ?)",
            (event_id, name.strip(), template, _now()),
        )
        campaign_id = int(cur.lastrowid)
        for cid in sorted(set(int(x) for x in contact_ids)):
            contact = conn.execute("SELECT * FROM event_contacts WHERE id=? AND event_id=?", (cid, event_id)).fetchone()
            if not contact:
                continue
            already_sent = conn.execute(
                """
                SELECT 1
                FROM whatsapp_campaign_recipients r
                JOIN whatsapp_campaigns c ON c.id=r.campaign_id AND c.event_id=r.event_id
                WHERE r.event_id=? AND r.contact_id=? AND r.status='sent' AND c.template=?
                LIMIT 1
                """,
                (event_id, cid, template),
            ).fetchone()
            status = "skipped" if already_sent else "pending"
            error = "Template já enviado anteriormente para este contato." if already_sent else None
            message_text = template
            conn.execute(
                """
                INSERT OR IGNORE INTO whatsapp_campaign_recipients(event_id, campaign_id, contact_id, phone, message_text, status, error_message, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, campaign_id, cid, contact["phone"], message_text, status, error, _now()),
            )
    audit_log(event_id, "whatsapp_campaign", campaign_id, "create", f"recipients={len(contact_ids)}")
    return campaign_id



def enqueue_campaign_recipient_message(event_id: int, recipient_id: int) -> int | None:
    """Cria/atualiza a fila padrão de mensagens para um destinatário de campanha.

    A campanha continua tendo sua própria trilha de status, mas o envio passa a ter
    lastro na tabela `messages`, que já é a fila central do WhatsApp do sistema.
    """
    init_db()
    with connect() as conn:
        event_id = _safe_event_id(event_id, conn)
        rec = conn.execute(
            """
            SELECT r.*, c.name AS contact_name, c.group_name, wc.template
            FROM whatsapp_campaign_recipients r
            JOIN event_contacts c ON c.event_id=r.event_id AND c.id=r.contact_id
            JOIN whatsapp_campaigns wc ON wc.event_id=r.event_id AND wc.id=r.campaign_id
            WHERE r.id=? AND r.event_id=?
            """,
            (int(recipient_id), event_id),
        ).fetchone()
        if not rec:
            return None
        if rec["message_id"]:
            msg = conn.execute("SELECT id FROM messages WHERE id=? AND event_id=?", (int(rec["message_id"]), event_id)).fetchone()
            if msg:
                return int(msg["id"])
        message_text = rec["message_text"] or rec["template"] or ""
        cur = conn.execute(
            """
            INSERT INTO messages(event_id, guest_id, group_name, guest_name, phone, table_name, template, message_text, status)
            VALUES (?, NULL, ?, ?, ?, '', ?, ?, 'pending')
            """,
            (event_id, rec["group_name"] or "", rec["contact_name"] or "", rec["phone"] or "", rec["template"] or "", message_text),
        )
        message_id = int(cur.lastrowid)
        conn.execute(
            "UPDATE whatsapp_campaign_recipients SET message_id=?, updated_at=? WHERE id=? AND event_id=?",
            (message_id, _now(), int(recipient_id), event_id),
        )
    audit_log(event_id, "whatsapp_campaign_recipient", recipient_id, "enqueue_message", f"message_id={message_id}")
    return message_id


def set_campaign_status(event_id: int, campaign_id: int, status: str) -> None:
    if status not in CAMPAIGN_STATUSES:
        raise ValueError("Status de campanha inválido.")
    init_db()
    with connect() as conn:
        conn.execute(
            "UPDATE whatsapp_campaigns SET status=?, updated_at=? WHERE id=? AND event_id=?",
            (status, _now(), int(campaign_id), int(event_id)),
        )


def campaign_report(event_id: int, campaign_id: int | None = None) -> dict:
    init_db()
    sql = """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent,
            SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) AS error,
            SUM(CASE WHEN status='skipped' THEN 1 ELSE 0 END) AS skipped
        FROM whatsapp_campaign_recipients
        WHERE event_id=?
    """
    params: list = [int(event_id)]
    if campaign_id:
        sql += " AND campaign_id=?"
        params.append(int(campaign_id))
    with connect() as conn:
        row = conn.execute(sql, tuple(params)).fetchone()
    return {k: int(row[k] or 0) for k in ["total", "pending", "sent", "error", "skipped"]} if row else {"total": 0, "pending": 0, "sent": 0, "error": 0, "skipped": 0}

def list_campaigns(event_id: int) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT c.*,
                   COUNT(r.id) AS total_recipients,
                   SUM(CASE WHEN r.status='sent' THEN 1 ELSE 0 END) AS sent_count,
                   SUM(CASE WHEN r.status='error' THEN 1 ELSE 0 END) AS error_count,
                   SUM(CASE WHEN r.status='pending' THEN 1 ELSE 0 END) AS pending_count,
                   SUM(CASE WHEN r.status='skipped' THEN 1 ELSE 0 END) AS skipped_count
            FROM whatsapp_campaigns c
            LEFT JOIN whatsapp_campaign_recipients r ON r.event_id=c.event_id AND r.campaign_id=c.id
            WHERE c.event_id=?
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """,
            (int(event_id),),
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def list_campaign_recipients(event_id: int, campaign_id: int | None = None, status: str | None = None) -> pd.DataFrame:
    init_db()
    sql = """
        SELECT r.*, c.name AS contact_name, c.group_name, c.email, c.tags, wc.name AS campaign_name, wc.template
        FROM whatsapp_campaign_recipients r
        JOIN event_contacts c ON c.event_id=r.event_id AND c.id=r.contact_id
        JOIN whatsapp_campaigns wc ON wc.event_id=r.event_id AND wc.id=r.campaign_id
        WHERE r.event_id=?
    """
    params: list = [int(event_id)]
    if campaign_id:
        sql += " AND r.campaign_id=?"
        params.append(int(campaign_id))
    if status and status != "todos":
        sql += " AND r.status=?"
        params.append(status)
    sql += " ORDER BY r.created_at DESC"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def update_campaign_recipient_status(event_id: int, recipient_id: int, status: str, error_message: str = "") -> None:
    if status not in RECIPIENT_STATUSES:
        raise ValueError("Status de destinatário inválido.")
    init_db()
    sent_at = _now() if status == "sent" else None
    with connect() as conn:
        conn.execute(
            """
            UPDATE whatsapp_campaign_recipients
            SET status=?, error_message=?, sent_at=COALESCE(?, sent_at), updated_at=?
            WHERE id=? AND event_id=?
            """,
            (status, error_message, sent_at, _now(), int(recipient_id), int(event_id)),
        )
        row = conn.execute(
            """
            SELECT campaign_id,
                   SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) AS pending_count,
                   SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) AS error_count
            FROM whatsapp_campaign_recipients WHERE event_id=? AND id=? GROUP BY campaign_id
            """,
            (int(event_id), int(recipient_id)),
        ).fetchone()
        if row:
            stats = conn.execute(
                "SELECT SUM(status='pending') AS pending_count, SUM(status='error') AS error_count FROM whatsapp_campaign_recipients WHERE event_id=? AND campaign_id=?",
                (int(event_id), int(row["campaign_id"])),
            ).fetchone()
            new_status = "queued"
            if stats and int(stats["pending_count"] or 0) == 0:
                new_status = "partial_error" if int(stats["error_count"] or 0) else "done"
            conn.execute("UPDATE whatsapp_campaigns SET status=?, updated_at=? WHERE id=? AND event_id=?", (new_status, _now(), int(row["campaign_id"]), int(event_id)))


def campaign_dashboard_metrics(event_id: int) -> dict:
    init_db()
    with connect() as conn:
        contacts = conn.execute(
            "SELECT COUNT(*) total, SUM(is_valid=1) valid, SUM(is_valid=0) invalid FROM event_contacts WHERE event_id=?",
            (int(event_id),),
        ).fetchone()
        campaigns = conn.execute("SELECT COUNT(*) total FROM whatsapp_campaigns WHERE event_id=?", (int(event_id),)).fetchone()
        recipients = conn.execute(
            "SELECT SUM(status='sent') sent, SUM(status='error') errors FROM whatsapp_campaign_recipients WHERE event_id=?",
            (int(event_id),),
        ).fetchone()
    return {
        "total_contacts": int(contacts["total"] or 0) if contacts else 0,
        "valid_contacts": int(contacts["valid"] or 0) if contacts else 0,
        "invalid_contacts": int(contacts["invalid"] or 0) if contacts else 0,
        "campaigns": int(campaigns["total"] or 0) if campaigns else 0,
        "sent_messages": int(recipients["sent"] or 0) if recipients else 0,
        "errors": int(recipients["errors"] or 0) if recipients else 0,
    }
