-- AI Loyalty Management Platform
-- PostgreSQL starter schema.
-- Apply to a fresh database. Existing FastAPI starter models use the same core
-- table names and compatible core columns. Review before applying to a database
-- that already contains data.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Identity, authentication and RBAC
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'customer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS permissions (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id BIGINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- 2. Loyalty organization and customer structure
CREATE TABLE IF NOT EXISTS customers (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    customer_code VARCHAR(50) NOT NULL UNIQUE,
    phone VARCHAR(30),
    date_of_birth DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS outlets (
    id BIGSERIAL PRIMARY KEY,
    outlet_code VARCHAR(50) NOT NULL UNIQUE,
    outlet_name VARCHAR(150) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS brands (
    id BIGSERIAL PRIMARY KEY,
    brand_code VARCHAR(50) NOT NULL UNIQUE,
    brand_name VARCHAR(150) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS portfolios (
    id BIGSERIAL PRIMARY KEY,
    portfolio_code VARCHAR(30) NOT NULL UNIQUE,
    portfolio_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_hierarchy_mapping (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    supervisor_user_id BIGINT REFERENCES users(id),
    outlet_id BIGINT REFERENCES outlets(id),
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    CHECK (valid_to IS NULL OR valid_to >= valid_from)
);

CREATE TABLE IF NOT EXISTS customer_outlet_mapping (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    outlet_id BIGINT NOT NULL REFERENCES outlets(id),
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    CHECK (valid_to IS NULL OR valid_to >= valid_from)
);

-- 3. Loyalty programs, tiers and points rules
CREATE TABLE IF NOT EXISTS loyalty_programs (
    id BIGSERIAL PRIMARY KEY,
    program_code VARCHAR(50) NOT NULL UNIQUE,
    program_name VARCHAR(150) NOT NULL,
    description TEXT,
    starts_on DATE,
    ends_on DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (ends_on IS NULL OR starts_on IS NULL OR ends_on >= starts_on)
);

CREATE TABLE IF NOT EXISTS loyalty_tiers (
    id BIGSERIAL PRIMARY KEY,
    program_id BIGINT NOT NULL REFERENCES loyalty_programs(id),
    tier_code VARCHAR(30) NOT NULL,
    tier_name VARCHAR(80) NOT NULL,
    minimum_points BIGINT NOT NULL DEFAULT 0 CHECK (minimum_points >= 0),
    benefits JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (program_id, tier_code)
);

CREATE TABLE IF NOT EXISTS customer_loyalty_accounts (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    program_id BIGINT NOT NULL REFERENCES loyalty_programs(id),
    tier_id BIGINT REFERENCES loyalty_tiers(id),
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    UNIQUE (customer_id, program_id)
);

CREATE TABLE IF NOT EXISTS points_structure (
    id BIGSERIAL PRIMARY KEY,
    program_id BIGINT NOT NULL REFERENCES loyalty_programs(id),
    brand_id BIGINT REFERENCES brands(id),
    portfolio_id BIGINT REFERENCES portfolios(id),
    amount_per_point NUMERIC(14,2) NOT NULL CHECK (amount_per_point > 0),
    points_per_unit NUMERIC(14,4) NOT NULL DEFAULT 1 CHECK (points_per_unit >= 0),
    cap_points BIGINT CHECK (cap_points IS NULL OR cap_points >= 0),
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    CHECK (valid_to IS NULL OR valid_to >= valid_from)
);

CREATE TABLE IF NOT EXISTS customer_points (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    program_id BIGINT NOT NULL REFERENCES loyalty_programs(id),
    current_balance BIGINT NOT NULL DEFAULT 0 CHECK (current_balance >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (customer_id, program_id)
);

CREATE TABLE IF NOT EXISTS points_transactions (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    program_id BIGINT REFERENCES loyalty_programs(id),
    points INTEGER NOT NULL CHECK (points > 0),
    transaction_type VARCHAR(20) NOT NULL
        CHECK (transaction_type IN ('earn', 'redeem', 'adjustment', 'expire', 'reversal')),
    reference_type VARCHAR(40),
    reference_id VARCHAR(80),
    description VARCHAR(255) NOT NULL DEFAULT '',
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Sales, targets and achievements
CREATE TABLE IF NOT EXISTS sales_transactions (
    id BIGSERIAL PRIMARY KEY,
    external_transaction_id VARCHAR(100) UNIQUE,
    outlet_id BIGINT NOT NULL REFERENCES outlets(id),
    brand_id BIGINT REFERENCES brands(id),
    portfolio_id BIGINT REFERENCES portfolios(id),
    customer_id BIGINT REFERENCES customers(id),
    gross_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    net_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    transaction_at TIMESTAMPTZ NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loyalty_targets (
    id BIGSERIAL PRIMARY KEY,
    outlet_id BIGINT NOT NULL REFERENCES outlets(id),
    brand_id BIGINT REFERENCES brands(id),
    portfolio_id BIGINT REFERENCES portfolios(id),
    target_period DATE NOT NULL,
    target_amount NUMERIC(14,2) NOT NULL CHECK (target_amount >= 0),
    created_by BIGINT REFERENCES users(id),
    UNIQUE (outlet_id, brand_id, portfolio_id, target_period)
);

CREATE TABLE IF NOT EXISTS target_achievements (
    id BIGSERIAL PRIMARY KEY,
    outlet_id BIGINT NOT NULL REFERENCES outlets(id),
    brand_id BIGINT REFERENCES brands(id),
    portfolio_id BIGINT REFERENCES portfolios(id),
    achievement_period DATE NOT NULL,
    sales_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    points_earned BIGINT NOT NULL DEFAULT 0,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Rewards, orders, redemptions and refunds
CREATE TABLE IF NOT EXISTS rewards (
    id BIGSERIAL PRIMARY KEY,
    reward_code VARCHAR(50) NOT NULL UNIQUE,
    reward_name VARCHAR(150) NOT NULL,
    description TEXT,
    points_required BIGINT NOT NULL CHECK (points_required > 0),
    inventory_quantity INTEGER CHECK (inventory_quantity IS NULL OR inventory_quantity >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    status VARCHAR(30) NOT NULL DEFAULT 'placed'
        CHECK (status IN ('placed', 'processing', 'shipped', 'delivered', 'cancelled', 'failed')),
    reward_name VARCHAR(150) NOT NULL,
    points_used INTEGER NOT NULL CHECK (points_used > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    reward_id BIGINT REFERENCES rewards(id),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    points_each BIGINT NOT NULL CHECK (points_each > 0)
);

CREATE TABLE IF NOT EXISTS redemptions (
    id BIGSERIAL PRIMARY KEY,
    redemption_number VARCHAR(60) NOT NULL UNIQUE,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    reward_id BIGINT REFERENCES rewards(id),
    order_id BIGINT REFERENCES orders(id),
    points_redeemed BIGINT NOT NULL CHECK (points_redeemed > 0),
    status VARCHAR(30) NOT NULL DEFAULT 'initiated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS redemption_transactions (
    id BIGSERIAL PRIMARY KEY,
    redemption_id BIGINT NOT NULL REFERENCES redemptions(id),
    provider VARCHAR(80),
    provider_reference VARCHAR(120),
    status VARCHAR(30) NOT NULL,
    request_payload JSONB,
    response_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cancellation_requests (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    requested_by BIGINT NOT NULL REFERENCES users(id),
    reason TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    confirmed_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS refund_transactions (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    points_refunded BIGINT NOT NULL DEFAULT 0 CHECK (points_refunded >= 0),
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    reference_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. RAG knowledge base and chatbot conversations
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    document_type VARCHAR(50),
    uploaded_by BIGINT REFERENCES users(id),
    access_scope VARCHAR(30) NOT NULL DEFAULT 'all',
    status VARCHAR(30) NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Requires the pgvector extension. Adjust vector dimension to the embedding model used.
CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    title VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL CHECK (sender IN ('user', 'assistant', 'tool')),
    message TEXT NOT NULL,
    citations JSONB NOT NULL DEFAULT '[]'::jsonb,
    token_usage JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Agent orchestration, approvals and audit
CREATE TABLE IF NOT EXISTS agent_tasks (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL UNIQUE,
    user_id BIGINT REFERENCES users(id),
    agent_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    input_payload JSONB,
    output_payload JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_approvals (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL REFERENCES agent_tasks(id),
    requested_by BIGINT REFERENCES users(id),
    decision_by BIGINT REFERENCES users(id),
    action_type VARCHAR(100) NOT NULL,
    action_payload JSONB NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_tool_calls (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT REFERENCES agent_tasks(id),
    tool_name VARCHAR(150) NOT NULL,
    input_payload JSONB,
    output_payload JSONB,
    status VARCHAR(30) NOT NULL,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    agent_name VARCHAR(100),
    action VARCHAR(150) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    outcome VARCHAR(30) NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Useful indexes
CREATE INDEX IF NOT EXISTS ix_points_customer_created
    ON points_transactions(customer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_orders_customer_created
    ON orders(customer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_sales_outlet_date
    ON sales_transactions(outlet_id, transaction_at);
CREATE INDEX IF NOT EXISTS ix_targets_period
    ON loyalty_targets(target_period);
CREATE INDEX IF NOT EXISTS ix_chat_session_created
    ON chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS ix_agent_tasks_status
    ON agent_tasks(status, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_document_chunks_document
    ON document_chunks(document_id);

-- Seed baseline role names (permissions should be assigned deliberately).
INSERT INTO roles (name, description) VALUES
    ('customer', 'Customer portal access'),
    ('outlet_user', 'Assigned outlet access'),
    ('supervisor', 'Assigned team and outlet reporting access'),
    ('support', 'Customer support operations'),
    ('admin', 'Platform administration')
ON CONFLICT (name) DO NOTHING;
