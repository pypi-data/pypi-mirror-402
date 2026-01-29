"""Generate comprehensive Storage Architecture PDF for Omni Cortex - Compact Version."""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Colors matching existing PDF style
PRIMARY = colors.HexColor('#4A90D9')  # Blue header
PRIMARY_DARK = colors.HexColor('#1F4E79')  # Dark blue for accents
TEXT = colors.HexColor('#333333')
LIGHT_BG = colors.HexColor('#F2F2F2')
WHITE = colors.white


def create_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=26,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica',
        fontSize=12,
        textColor=PRIMARY_DARK,
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        'SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        'SubHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=PRIMARY_DARK,
        spaceBefore=8,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'Body',
        fontName='Helvetica',
        fontSize=9,
        textColor=TEXT,
        spaceAfter=6,
        leading=12
    ))

    styles.add(ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=WHITE,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=8,
        textColor=TEXT
    ))

    styles.add(ParagraphStyle(
        'Footer',
        fontName='Helvetica',
        fontSize=8,
        textColor=TEXT,
        alignment=TA_CENTER
    ))

    return styles


def create_table(data, col_widths=None, header_color=PRIMARY, font_size=8):
    """Create a styled table."""
    if col_widths is None:
        col_widths = [1.4*inch, 0.9*inch, 3.2*inch]

    table = Table(data, colWidths=col_widths)

    style = [
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), font_size),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), font_size),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]

    # Alternating row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), LIGHT_BG))

    table.setStyle(TableStyle(style))
    return table


def header_footer(canvas, doc):
    """Add header and footer to each page."""
    canvas.saveState()

    # Header
    canvas.setFillColor(PRIMARY_DARK)
    canvas.setFont('Helvetica', 9)
    canvas.drawString(54, 756, "Storage Architecture")
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(54, 750, 558, 750)

    # Footer
    canvas.setFillColor(TEXT)
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(306, 30, f"Page {doc.page}")

    canvas.restoreState()


def build_document():
    """Build the complete PDF document."""
    doc = SimpleDocTemplate(
        "D:/Projects/omni-cortex/docs/06_OmniCortex_StorageArchitecture.pdf",
        pagesize=letter,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
        topMargin=0.8*inch,
        bottomMargin=0.6*inch
    )

    styles = create_styles()
    elements = []

    # ===== PAGE 1: TITLE, OVERVIEW, AND CORE TABLES =====
    elements.append(Paragraph("OmniCortex Storage Architecture", styles['DocTitle']))
    elements.append(Paragraph("Technical Reference", styles['DocSubtitle']))

    elements.append(Paragraph(
        "OmniCortex uses SQLite for all data storage - prioritizing simplicity, portability, "
        "and reliability. Single-file databases with FTS5 full-text search, ACID compliance, "
        "and zero configuration required.",
        styles['Body']
    ))

    # Storage Locations
    elements.append(Paragraph("Storage Locations", styles['SectionHeader']))
    locations_data = [
        ['Location', 'Path', 'Purpose'],
        ['Project DB', '.omni-cortex/cortex.db', 'Memories, activities, sessions'],
        ['Global DB', '~/.omni-cortex/global.db', 'Cross-project search index'],
        ['Config', '.omni-cortex/config.yaml', 'Project settings'],
        ['Dashboard', '~/.omni-cortex/projects.json', 'Favorites, scan dirs'],
    ]
    elements.append(create_table(locations_data, [1.1*inch, 1.8*inch, 2.6*inch]))

    # Database Tables Overview
    elements.append(Paragraph("Database Tables Overview (12 Tables, ~100 Fields)", styles['SectionHeader']))
    tables_data = [
        ['Table', 'Purpose', 'Fields'],
        ['memories', 'Knowledge/learnings storage', '20'],
        ['activities', 'Tool call audit trail', '19'],
        ['sessions', 'Work session groupings', '7'],
        ['agents', 'Claude Code agent tracking', '7'],
        ['memory_relationships', 'Links between memories', '6'],
        ['activity_memory_links', 'Cross-references', '4'],
        ['embeddings', 'Vector search (optional)', '6'],
        ['session_summaries', 'Computed session stats', '9'],
        ['style_markers', 'Writing style patterns (v1.13+)', '5'],
        ['user_messages', 'Communication samples (v1.13+)', '5'],
        ['config', 'System configuration', '3'],
        ['global_memories', 'Cross-project index', '9'],
    ]
    elements.append(create_table(tables_data, [1.6*inch, 2.8*inch, 0.6*inch]))

    # memories Table
    elements.append(Paragraph("memories Table (Complete Schema)", styles['SectionHeader']))
    memories_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'mem_{timestamp}_{hex}'],
        ['content', 'TEXT', 'Main memory content (required)'],
        ['context', 'TEXT', 'Additional context'],
        ['type', 'TEXT', 'Auto-detected category'],
        ['tags', 'TEXT', 'JSON array of tags'],
        ['status', 'TEXT', 'fresh/needs_review/outdated/archived'],
        ['importance_score', 'REAL', 'Calculated 0-100 with decay'],
        ['manual_importance', 'INTEGER', 'User override 1-100'],
        ['created_at', 'TEXT', 'ISO 8601 timestamp'],
        ['updated_at', 'TEXT', 'ISO 8601 timestamp'],
        ['last_accessed', 'TEXT', 'ISO 8601 timestamp'],
        ['last_verified', 'TEXT', 'ISO 8601 timestamp'],
        ['access_count', 'INTEGER', 'Times accessed'],
        ['source_session_id', 'TEXT FK', 'Session that created it'],
        ['source_agent_id', 'TEXT FK', 'Agent that created it'],
        ['source_activity_id', 'TEXT FK', 'Triggering activity'],
        ['project_path', 'TEXT', 'Project context'],
        ['file_context', 'TEXT', 'JSON array of files'],
        ['has_embedding', 'INTEGER', 'Boolean: has vector'],
        ['metadata', 'TEXT', 'JSON extensibility'],
    ]
    elements.append(create_table(memories_data, [1.4*inch, 0.9*inch, 3.2*inch]))

    elements.append(PageBreak())

    # ===== PAGE 2: MEMORY TYPES + ACTIVITIES TABLE =====
    elements.append(Paragraph("Memory Types (Auto-Detected)", styles['SectionHeader']))
    types_data = [
        ['Type', 'Description', 'Trigger Keywords'],
        ['warning', 'Cautions, things to avoid', '"warning", "caution", "avoid", "never"'],
        ['tip', 'Tips, best practices', '"tip", "trick", "best practice"'],
        ['config', 'Configuration/settings', '"config", "setting", "environment"'],
        ['troubleshooting', 'Debugging guides', '"debug", "troubleshoot", "investigate"'],
        ['code', 'Code snippets', '"function", "class", "algorithm"'],
        ['error', 'Errors, failures', '"error", "exception", "failed"'],
        ['solution', 'Working fixes', '"solution", "fix", "resolved"'],
        ['command', 'CLI commands', '"run", "execute", "command"'],
        ['concept', 'Definitions', '"concept", "definition", "what is"'],
        ['decision', 'Architectural choices', '"decided", "chose", "architecture"'],
        ['general', 'Default category', '(fallback)'],
    ]
    elements.append(create_table(types_data, [1.1*inch, 1.6*inch, 2.8*inch]))

    # activities Table
    elements.append(Paragraph("activities Table (Complete Schema)", styles['SectionHeader']))
    activities_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'act_{timestamp}_{hex}'],
        ['session_id', 'TEXT FK', 'Session grouping'],
        ['agent_id', 'TEXT FK', 'Agent reference'],
        ['timestamp', 'TEXT', 'ISO 8601 event time'],
        ['event_type', 'TEXT', 'pre_tool_use/post_tool_use/decision/observation'],
        ['tool_name', 'TEXT', 'Name of tool called'],
        ['tool_input', 'TEXT', 'JSON input (truncated 10KB)'],
        ['tool_output', 'TEXT', 'JSON output (truncated 10KB)'],
        ['duration_ms', 'INTEGER', 'Execution time in ms'],
        ['success', 'INTEGER', '1=success, 0=failure'],
        ['error_message', 'TEXT', 'Error details if failed'],
        ['project_path', 'TEXT', 'Project context'],
        ['file_path', 'TEXT', 'Relevant file'],
        ['command_name', 'TEXT', 'Slash command (v1.3+)'],
        ['command_scope', 'TEXT', 'universal/project (v1.3+)'],
        ['mcp_server', 'TEXT', 'MCP server name (v1.3+)'],
        ['skill_name', 'TEXT', 'Skill name (v1.3+)'],
        ['summary', 'TEXT', 'NLP summary (v1.2+)'],
        ['metadata', 'TEXT', 'JSON extensibility'],
    ]
    elements.append(create_table(activities_data, [1.4*inch, 0.9*inch, 3.2*inch]))

    # Event Types (compact)
    elements.append(Paragraph("Event Types", styles['SubHeader']))
    events_data = [
        ['Type', 'Description'],
        ['pre_tool_use', 'Before tool execution - captures intent'],
        ['post_tool_use', 'After tool completion - captures results'],
        ['decision', 'Human/agent decision point'],
        ['observation', 'Discovery or finding during exploration'],
    ]
    elements.append(create_table(events_data, [1.3*inch, 4.2*inch]))

    elements.append(PageBreak())

    # ===== PAGE 3: SESSIONS, AGENTS, RELATIONSHIPS, SUMMARIES =====
    elements.append(Paragraph("sessions Table", styles['SectionHeader']))
    sessions_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'sess_{timestamp}_{hex}'],
        ['project_path', 'TEXT', 'Project directory path'],
        ['started_at', 'TEXT', 'ISO 8601 start time'],
        ['ended_at', 'TEXT', 'ISO 8601 end time (nullable)'],
        ['summary', 'TEXT', 'Auto or manual summary'],
        ['tags', 'TEXT', 'JSON array of tags'],
        ['metadata', 'TEXT', 'JSON extensibility'],
    ]
    elements.append(create_table(sessions_data))

    elements.append(Paragraph("agents Table", styles['SectionHeader']))
    agents_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'Agent ID from Claude Code'],
        ['name', 'TEXT', 'Optional agent name'],
        ['type', 'TEXT', 'main, subagent, or tool'],
        ['first_seen', 'TEXT', 'ISO 8601 first activity'],
        ['last_seen', 'TEXT', 'ISO 8601 last activity'],
        ['total_activities', 'INTEGER', 'Activity count'],
        ['metadata', 'TEXT', 'JSON extensibility'],
    ]
    elements.append(create_table(agents_data))

    elements.append(Paragraph("memory_relationships Table", styles['SectionHeader']))
    relationships_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'rel_{timestamp}_{hex}'],
        ['source_id', 'TEXT FK', 'Source memory ID'],
        ['target_id', 'TEXT FK', 'Target memory ID'],
        ['relationship_type', 'TEXT', 'related_to/supersedes/derived_from/contradicts'],
        ['strength', 'REAL', 'Strength 0.0-1.0'],
        ['created_at', 'TEXT', 'ISO 8601 timestamp'],
    ]
    elements.append(create_table(relationships_data))

    # Relationship Types (inline)
    rel_types_data = [
        ['Type', 'Description'],
        ['related_to', 'General association between memories'],
        ['supersedes', 'New memory replaces/updates old one'],
        ['derived_from', 'New memory based on or extends old'],
        ['contradicts', 'Memories have conflicting information'],
    ]
    elements.append(create_table(rel_types_data, [1.3*inch, 4.2*inch]))

    elements.append(Paragraph("session_summaries Table", styles['SectionHeader']))
    summaries_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'sum_{timestamp}_{hex}'],
        ['session_id', 'TEXT FK', 'Session reference'],
        ['key_learnings', 'TEXT', 'JSON array of learnings'],
        ['key_decisions', 'TEXT', 'JSON array of decisions'],
        ['key_errors', 'TEXT', 'JSON array of errors (max 10)'],
        ['files_modified', 'TEXT', 'JSON array of file paths'],
        ['tools_used', 'TEXT', 'JSON {tool_name: count}'],
        ['total_activities', 'INTEGER', 'Activity count'],
        ['total_memories_created', 'INTEGER', 'Memories created'],
    ]
    elements.append(create_table(summaries_data))

    elements.append(PageBreak())

    # ===== PAGE 4: EMBEDDINGS, LINKS, STYLE, GLOBAL, FTS =====
    elements.append(Paragraph("embeddings Table (Optional)", styles['SectionHeader']))
    embeddings_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'emb_{timestamp}_{hex}'],
        ['memory_id', 'TEXT FK', 'Memory reference (unique)'],
        ['model_name', 'TEXT', 'Model (default: all-MiniLM-L6-v2)'],
        ['vector', 'BLOB', 'float32 array (384 dimensions)'],
        ['dimensions', 'INTEGER', '384 for default model'],
        ['created_at', 'TEXT', 'ISO 8601 timestamp'],
    ]
    elements.append(create_table(embeddings_data))

    elements.append(Paragraph("activity_memory_links Table", styles['SectionHeader']))
    links_data = [
        ['Column', 'Type', 'Description'],
        ['activity_id', 'TEXT FK', 'Activity reference'],
        ['memory_id', 'TEXT FK', 'Memory reference'],
        ['link_type', 'TEXT', 'created/accessed/updated/referenced'],
        ['created_at', 'TEXT', 'ISO 8601 timestamp'],
    ]
    elements.append(create_table(links_data))

    elements.append(Paragraph("style_markers Table (v1.13+)", styles['SectionHeader']))
    style_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'Marker identifier'],
        ['marker_type', 'TEXT', 'phrase/pattern/characteristic'],
        ['content', 'TEXT', 'The style marker content'],
        ['platform', 'TEXT', 'Associated platform (optional)'],
        ['created_at', 'TEXT', 'ISO 8601 timestamp'],
    ]
    elements.append(create_table(style_data))

    elements.append(Paragraph("user_messages Table (v1.13+)", styles['SectionHeader']))
    messages_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'Message identifier'],
        ['content', 'TEXT', 'The message content'],
        ['platform', 'TEXT', 'Platform (skool, email, dm, etc.)'],
        ['context_type', 'TEXT', 'Type of communication'],
        ['created_at', 'TEXT', 'ISO 8601 timestamp'],
    ]
    elements.append(create_table(messages_data))

    elements.append(Paragraph("Global Index (Cross-Project Search)", styles['SectionHeader']))
    global_data = [
        ['Column', 'Type', 'Description'],
        ['memory_id', 'TEXT PK', 'Original memory ID'],
        ['project_path', 'TEXT', 'Source project path'],
        ['content', 'TEXT', 'Memory content (synced)'],
        ['context', 'TEXT', 'Memory context (synced)'],
        ['memory_type', 'TEXT', 'Memory type'],
        ['tags', 'TEXT', 'JSON tags array'],
        ['importance_score', 'REAL', 'Importance at sync'],
        ['status', 'TEXT', 'Memory status'],
        ['synced_at', 'TEXT', 'ISO 8601 sync time'],
    ]
    elements.append(create_table(global_data))

    elements.append(Paragraph("Full-Text Search (FTS5)", styles['SectionHeader']))
    fts_data = [
        ['Feature', 'Details'],
        ['Index', 'memories_fts (content, context, tags)'],
        ['Tokenizer', 'Porter stemmer + Unicode61'],
        ['Capabilities', 'Phrase matching, prefix search, AND/OR/NOT, BM25 ranking'],
    ]
    elements.append(create_table(fts_data, [1.3*inch, 4.2*inch]))

    elements.append(PageBreak())

    # ===== PAGE 5: IMPORTANCE, SEARCH, CONFIG, INDEXES =====
    elements.append(Paragraph("Importance Decay System", styles['SectionHeader']))
    elements.append(Paragraph(
        "Memory importance scores decay over time to prioritize fresh, relevant information:",
        styles['Body']
    ))
    decay_data = [
        ['Factor', 'Formula/Value', 'Description'],
        ['Base Importance', 'manual or calculated', 'Starting score (1-100)'],
        ['Time Decay', '-0.5 points/day', 'Configurable decay_rate_per_day'],
        ['Access Boost', 'log(count + 1) × 5', 'More access = higher score'],
        ['Freshness', '+10/0/-10/-30', 'fresh/review/outdated/archived'],
        ['Final Score', 'max(0, min(100, calc))', 'Clamped to 0-100'],
    ]
    elements.append(create_table(decay_data, [1.4*inch, 1.6*inch, 2.5*inch]))

    elements.append(Paragraph("Search Relevance Scoring", styles['SectionHeader']))
    search_data = [
        ['Factor', 'Weight', 'Max Points'],
        ['Keyword Match (FTS5 BM25)', '40%', '40'],
        ['Semantic Similarity', '40%', '40'],
        ['Access Frequency', 'log scale', '20'],
        ['Recency (30-day decay)', 'exponential', '15'],
        ['Importance Score', 'scaled', '15'],
        ['Exact Phrase Match', 'bonus', '+10'],
    ]
    elements.append(create_table(search_data, [2.4*inch, 1.4*inch, 1.2*inch]))

    elements.append(Paragraph("Configuration Options (.omni-cortex/config.yaml)", styles['SectionHeader']))
    config_data = [
        ['Setting', 'Default', 'Description'],
        ['schema_version', '6', 'Database schema version'],
        ['embedding_enabled', 'false', 'Enable semantic search'],
        ['embedding_model', 'all-MiniLM-L6-v2', 'Vector model'],
        ['decay_rate_per_day', '0.5', 'Importance decay rate'],
        ['freshness_review_days', '30', 'Days until needs_review'],
        ['max_output_truncation', '10000', 'Output truncation limit'],
        ['auto_provide_context', 'true', 'Session context on start'],
        ['context_depth', '3', 'Past sessions to summarize'],
        ['default_search_mode', 'keyword', 'keyword/semantic/hybrid'],
        ['global_sync_enabled', 'true', 'Cross-project sync'],
        ['api_fallback_enabled', 'false', 'API fallback for embeddings'],
    ]
    elements.append(create_table(config_data, [1.8*inch, 1.4*inch, 2.3*inch]))

    elements.append(Paragraph("Database Indexes", styles['SectionHeader']))
    indexes_data = [
        ['Index', 'Table', 'Column(s)'],
        ['idx_activities_session', 'activities', 'session_id'],
        ['idx_activities_agent', 'activities', 'agent_id'],
        ['idx_activities_timestamp', 'activities', 'timestamp DESC'],
        ['idx_activities_tool', 'activities', 'tool_name'],
        ['idx_memories_type', 'memories', 'type'],
        ['idx_memories_status', 'memories', 'status'],
        ['idx_memories_project', 'memories', 'project_path'],
        ['idx_memories_importance', 'memories', 'importance_score DESC'],
        ['idx_memories_accessed', 'memories', 'last_accessed DESC'],
        ['idx_relationships_source', 'memory_relationships', 'source_id'],
        ['idx_relationships_target', 'memory_relationships', 'target_id'],
    ]
    elements.append(create_table(indexes_data, [2*inch, 1.8*inch, 1.7*inch]))

    elements.append(PageBreak())

    # ===== PAGE 6: AUTO-TAGS, STATUS, BACKUP, IDS, SECURITY =====
    elements.append(Paragraph("Auto-Tagging Categories", styles['SectionHeader']))
    tags_data = [
        ['Category', 'Example Tags'],
        ['Languages', 'python, javascript, typescript, rust, go, java, cpp, ruby, sql, shell'],
        ['Frameworks', 'react, vue, angular, nextjs, fastapi, django, flask, express, rails'],
        ['Tools', 'git, docker, kubernetes, aws, gcp, azure, terraform, npm, pip, vscode'],
        ['Concepts', 'api, database, auth, testing, security, performance, async, regex, config'],
        ['Project Types', 'frontend, backend, fullstack, cli, mobile, web'],
    ]
    elements.append(create_table(tags_data, [1.3*inch, 4.2*inch]))

    elements.append(Paragraph("Memory Status Lifecycle", styles['SectionHeader']))
    status_data = [
        ['Status', 'Description', 'Trigger'],
        ['fresh', 'Recently created/verified', 'New or manual verification'],
        ['needs_review', 'May be outdated', '30+ days without verification'],
        ['outdated', 'Confirmed outdated', '60+ days or manual marking'],
        ['archived', 'No longer relevant', 'Manual, excluded from search'],
    ]
    elements.append(create_table(status_data, [1.2*inch, 2*inch, 2.3*inch]))

    elements.append(Paragraph("Dashboard Config (~/.omni-cortex/projects.json)", styles['SectionHeader']))
    dashboard_data = [
        ['Field', 'Type', 'Description'],
        ['version', 'integer', 'Config schema version'],
        ['scan_directories', 'string[]', 'Directories to scan for projects'],
        ['registered_projects', 'object[]', 'Manual projects (path, display_name, added_at)'],
        ['favorites', 'string[]', 'Favorite project paths'],
        ['recent', 'object[]', 'Recent projects (path, last_accessed)'],
    ]
    elements.append(create_table(dashboard_data, [1.6*inch, 1*inch, 2.9*inch]))

    elements.append(Paragraph("Backup & Migration", styles['SectionHeader']))
    backup_data = [
        ['Operation', 'Method'],
        ['Project Backup', 'Copy .omni-cortex/ directory'],
        ['Global Backup', 'Copy ~/.omni-cortex/ directory'],
        ['Migration', 'Move directories - no reconfiguration'],
        ['JSON Export', 'cortex_export format="json"'],
        ['Markdown Export', 'cortex_export format="markdown"'],
        ['SQLite Backup', 'cortex_export format="sqlite" output_path="backup.db"'],
    ]
    elements.append(create_table(backup_data, [1.5*inch, 4*inch]))

    elements.append(Paragraph("ID Generation Formats", styles['SectionHeader']))
    ids_data = [
        ['Entity', 'Format', 'Example'],
        ['Memory', 'mem_{ts}_{hex}', 'mem_1736285432123_5c83106d'],
        ['Activity', 'act_{ts}_{hex}', 'act_1736285432456_9de1a644'],
        ['Session', 'sess_{ts}_{hex}', 'sess_1736285432789_3f2a8b1c'],
        ['Relationship', 'rel_{ts}_{hex}', 'rel_1736285433012_7c4d9e2f'],
        ['Embedding', 'emb_{ts}_{hex}', 'emb_1736285433345_1a5b3c7d'],
        ['Summary', 'sum_{ts}_{hex}', 'sum_1736285433678_8e9f0a1b'],
    ]
    elements.append(create_table(ids_data, [1.2*inch, 1.5*inch, 2.8*inch]))

    elements.append(Paragraph("Security & Validation", styles['SectionHeader']))
    security_data = [
        ['Measure', 'Implementation'],
        ['Input Truncation', 'Tool inputs/outputs capped at 10KB'],
        ['JSON Safety', 'Safe truncation with fallback handling'],
        ['SQL Injection', 'Prepared statements with parameter binding'],
        ['FTS5 Escaping', 'Query sanitization prevents injection'],
        ['Type Validation', 'Pydantic models enforce schema'],
    ]
    elements.append(create_table(security_data, [1.5*inch, 4*inch]))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "OmniCortex v1.14.0 | github.com/anthropics/omni-cortex",
        styles['Footer']
    ))

    # Build the PDF
    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    print("PDF generated successfully!")


if __name__ == "__main__":
    build_document()
