-- 成员5：智能客服 + 运营看板 数据库初始化
-- 与其他成员共享的 users 表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 成员1 文案历史（看板统计用）
CREATE TABLE IF NOT EXISTS history_writing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_features TEXT,
    platform VARCHAR(50),
    title TEXT,
    body TEXT,
    tags VARCHAR(500),
    language VARCHAR(20) DEFAULT 'zh',
    style VARCHAR(20) DEFAULT 'default',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 成员2 抠图历史
CREATE TABLE IF NOT EXISTS history_matte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    original_url VARCHAR(500) NOT NULL,
    matted_url VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    category_en VARCHAR(100),
    confidence FLOAT,
    attributes VARCHAR(200),
    file_size INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 成员3 背景历史
CREATE TABLE IF NOT EXISTS history_background (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_category VARCHAR(100) NOT NULL,
    style VARCHAR(50),
    color_hint VARCHAR(50),
    prompt_used TEXT,
    bg_url VARCHAR(500),
    enhanced_url VARCHAR(500),
    scale_factor INT DEFAULT 2,
    generation_time FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 成员4 海报历史
CREATE TABLE IF NOT EXISTS history_poster (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    matted_url VARCHAR(500) NOT NULL,
    bg_url VARCHAR(500) NOT NULL,
    template_id INTEGER,
    poster_url VARCHAR(500) NOT NULL,
    title VARCHAR(200),
    discount VARCHAR(50),
    price VARCHAR(50),
    ratio VARCHAR(20) DEFAULT '1:1',
    downloads INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 成员5 客服会话
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) DEFAULT '新会话',
    doc_name VARCHAR(200),
    faiss_index_path VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'zh',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

CREATE TABLE IF NOT EXISTS chat_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    feedback_type VARCHAR(10) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES chat_messages(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS system_daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date DATE NOT NULL UNIQUE,
    total_users INT DEFAULT 0,
    writing_calls INT DEFAULT 0,
    matte_calls INT DEFAULT 0,
    bg_calls INT DEFAULT 0,
    poster_calls INT DEFAULT 0,
    chat_calls INT DEFAULT 0,
    error_count INT DEFAULT 0
);

-- ABO 商品知识库
CREATE TABLE IF NOT EXISTS abo_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id VARCHAR(20) NOT NULL UNIQUE,
    item_name TEXT,
    item_name_zh TEXT,
    brand TEXT,
    product_type VARCHAR(200),
    bullet_points TEXT,
    bullet_points_zh TEXT,
    material TEXT,
    color TEXT,
    faq_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 模块错误日志（异常预警用）
CREATE TABLE IF NOT EXISTS module_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_name VARCHAR(50) NOT NULL,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
