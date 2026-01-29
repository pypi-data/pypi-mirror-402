"""
Update OmniCortex PDF Documentation
Adds Response Composer, Style features, and other v1.10-v1.14 updates
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

# OmniCortex brand colors
PRIMARY = colors.HexColor('#4A90D9')  # Blue
SECONDARY = colors.HexColor('#5BA0E9')  # Lighter blue
ACCENT = colors.HexColor('#2ECC71')  # Green accent
TEXT_DARK = colors.HexColor('#333333')
TEXT_MUTED = colors.HexColor('#666666')
LIGHT_BG = colors.HexColor('#F5F7FA')
WHITE = colors.white

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')


def get_styles():
    """Create consistent styles for all PDFs"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=PRIMARY,
        spaceAfter=6,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica',
        fontSize=14,
        textColor=TEXT_MUTED,
        spaceAfter=30,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        'SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=PRIMARY,
        spaceBefore=20,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        'SubHeader',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=TEXT_DARK,
        spaceBefore=15,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        'OmniBody',
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_DARK,
        leading=14,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        'BulletItem',
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_DARK,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'CodeBlock',
        fontName='Courier',
        fontSize=9,
        textColor=TEXT_DARK,
        backColor=LIGHT_BG,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=5,
        spaceAfter=5
    ))

    styles.add(ParagraphStyle(
        'PageHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=TEXT_MUTED
    ))

    return styles


def header_footer(canvas, doc, title):
    """Add header and footer to pages"""
    canvas.saveState()

    # Header line
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(2)
    canvas.line(36, 756, 576, 756)

    # Header text
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(36, 762, title)

    # Footer
    canvas.setFont('Helvetica', 9)
    canvas.drawCentredString(306, 30, f"Page {doc.page}")

    canvas.restoreState()


def create_table(data, col_widths=None, header_color=PRIMARY):
    """Create a styled table"""
    if col_widths is None:
        col_widths = [1.5*inch] * len(data[0])

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table


def create_callout_box(text, styles, color=PRIMARY):
    """Create a colored callout box"""
    data = [[Paragraph(text, ParagraphStyle(
        'CalloutText',
        fontName='Courier',
        fontSize=9,
        textColor=WHITE,
        alignment=TA_CENTER
    ))]]
    table = Table(data, colWidths=[5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return table


# ============================================================================
# 1. DASHBOARD GUIDE PDF
# ============================================================================

def create_dashboard_guide():
    """Create the updated Dashboard Guide PDF"""
    styles = get_styles()
    filename = os.path.join(OUTPUT_DIR, 'OmniCortex_DashboardGuide.pdf')

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=50, bottomMargin=50
    )

    elements = []

    # Title page
    elements.append(Paragraph("OmniCortex Web Dashboard", styles['DocTitle']))
    elements.append(Paragraph("User Guide", styles['DocSubtitle']))

    elements.append(Paragraph(
        "The OmniCortex Dashboard is a visual interface for browsing, searching, and managing your "
        "memories. Built with Vue 3 and FastAPI, it provides real-time updates and powerful analytics.",
        styles['OmniBody']
    ))

    # Quick Start
    elements.append(Paragraph("Quick Start", styles['SectionHeader']))
    elements.append(create_callout_box("omni-cortex-dashboard<br/>Opens at http://localhost:8765", styles, ACCENT))
    elements.append(Spacer(1, 10))

    # Key Features - Two column layout
    elements.append(Paragraph("Key Features", styles['SectionHeader']))

    features_data = [
        ['Core Features', 'Data Management'],
        ['• 7 Feature Tabs\n• Real-time WebSocket updates\n• Project switching\n• Dark/Light theme support\n• Multi-project selector',
         '• Export to JSON, Markdown, CSV\n• Bulk status updates\n• Memory editing & deletion\n• Advanced filtering']
    ]
    features_table = Table(features_data, colWidths=[2.7*inch, 2.7*inch])
    features_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(features_table)
    elements.append(Spacer(1, 15))

    # Dashboard Tabs Overview
    elements.append(Paragraph("Dashboard Tabs Overview", styles['SectionHeader']))

    tabs_data = [
        ['Tab', 'Icon', 'Purpose'],
        ['Memories', 'Database', 'Browse, search, filter, and edit memories'],
        ['Activity', 'History', 'View complete audit trail of tool usage'],
        ['Statistics', 'BarChart', 'Analytics: heatmaps, charts, distributions'],
        ['Review', 'RefreshCw', 'Mark stale memories as fresh/outdated/archived'],
        ['Graph', 'Network', 'Visualize memory relationships with D3.js'],
        ['Ask AI', 'MessageSquare', 'Natural language queries with 3 modes (Chat/Compose/Generate)'],
        ['Style', 'Palette', 'Manage writing style profiles and markers'],
    ]
    elements.append(create_table(tabs_data, [1.2*inch, 1*inch, 3.3*inch]))

    elements.append(PageBreak())

    # Memories Tab
    elements.append(Paragraph("Memories Tab", styles['SectionHeader']))
    elements.append(Paragraph(
        "The Memory Browser is the primary interface for viewing and managing your stored knowledge.",
        styles['OmniBody']
    ))

    for item in [
        "<b>Infinite Scroll</b> - Loads 50+ memories at a time as you scroll",
        "<b>Advanced Filtering</b> - Filter by type, status, tags, importance range",
        "<b>Sorting Options</b> - Sort by last accessed, created date, importance, access count",
        "<b>Full-text Search</b> - Search in content and context with highlighting",
        "<b>Detail Panel</b> - Right sidebar shows full memory with edit/delete options",
        "<b>Export Options</b> - Copy as Markdown or download as JSON",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    # Activity Tab
    elements.append(Paragraph("Activity Tab", styles['SectionHeader']))
    elements.append(Paragraph(
        "Complete audit trail of every tool call made during your sessions.",
        styles['OmniBody']
    ))

    for item in [
        "<b>Event Type Filter</b> - pre_tool_use, post_tool_use, decision, observation",
        "<b>Tool Filter</b> - Filter by specific tool name",
        "<b>Status Indicators</b> - Success/failure badges with error messages",
        "<b>Timing Info</b> - Duration in ms/seconds, exact timestamps",
        "<b>Expandable Rows</b> - Click to view full JSON input/output with copy button",
        "<b>MCP Badges</b> - Shows which MCP server handled the tool call",
        "<b>Command/Skill Tags</b> - Visual badges for slash commands and skills",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    elements.append(create_callout_box(
        "Activity Stats: Total activities | Success count | Failed count",
        styles, SECONDARY
    ))

    # Statistics Tab
    elements.append(Paragraph("Statistics Tab", styles['SectionHeader']))
    elements.append(Paragraph(
        "Comprehensive analytics and visualizations for your memory data.",
        styles['OmniBody']
    ))

    stats_data = [
        ['Chart', 'Description'],
        ['Overview Cards', 'Total memories, average importance, total views'],
        ['Type Distribution', 'Horizontal bar chart showing memories per type'],
        ['Status Distribution', 'Progress bars for fresh/needs_review/outdated/archived'],
        ['Top Tags', 'Top 15 tags with usage counts (clickable)'],
        ['Activity Heatmap', '90-day GitHub-style calendar visualization'],
        ['Tool Usage Chart', 'Top 10 tools with success rate indicators'],
        ['Memory Growth', '30-day line chart: cumulative + daily new'],
    ]
    elements.append(create_table(stats_data, [1.8*inch, 3.7*inch]))

    elements.append(Paragraph("Command & Skill Analytics (v1.3.0+)", styles['SubHeader']))
    cmd_data = [
        ['Chart', 'Description'],
        ['Command Usage', 'Bar chart: slash commands by usage count, filterable by scope'],
        ['Skill Usage', 'Bar chart: skill adoption and success rates'],
        ['MCP Usage', 'Doughnut chart: MCP server integration metrics'],
    ]
    elements.append(create_table(cmd_data, [1.8*inch, 3.7*inch]))

    elements.append(PageBreak())

    # Ask AI Tab - Updated with 3 modes
    elements.append(Paragraph("Ask AI Tab", styles['SectionHeader']))
    elements.append(Paragraph(
        "Natural language queries about your memories using Gemini. The Ask AI panel now supports "
        "<b>three modes</b>: Chat, Compose, and Generate.",
        styles['OmniBody']
    ))

    elements.append(create_callout_box(
        "Setup Required: export GEMINI_API_KEY=your_api_key_here",
        styles, colors.HexColor('#E74C3C')
    ))
    elements.append(Spacer(1, 10))

    # Three modes
    elements.append(Paragraph("Chat Mode", styles['SubHeader']))
    for item in [
        "<b>Conversational Interface</b> - Multi-turn conversation history",
        "<b>Source Citations</b> - Responses cite which memories were used",
        "<b>Clickable Sources</b> - Click citations to navigate to memory",
        "<b>Example Prompts</b> - Suggested queries to get started",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    elements.append(Paragraph("Compose Mode (Response Composer) - NEW in v1.13.0", styles['SubHeader']))
    elements.append(Paragraph(
        "Generate AI-powered responses that match your personal writing style. Perfect for "
        "Skool posts, DMs, emails, and comments.",
        styles['OmniBody']
    ))

    for item in [
        "<b>Platform Context Selector</b> - Skool post, DM, Email, Comment, General",
        "<b>Response Templates</b> - Answer Question, Provide Guidance, Redirect to Resource, Acknowledge",
        "<b>Tone Slider</b> - Adjust from Very Casual (0) to Very Professional (100)",
        "<b>Style Profile Integration</b> - Uses your stored writing samples for voice matching",
        "<b>Memory Context</b> - Optionally include relevant memories in response generation",
        "<b>Custom Instructions</b> - Add specific requirements or questions to include (v1.14.0)",
        "<b>'Explain to Me' Mode</b> - Get explanation of incoming message before responding (v1.14.0)",
        "<b>Response History</b> - Last 5 responses with click-to-reload",
        "<b>Copy & Regenerate</b> - Quick actions for generated responses",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    elements.append(Paragraph("Generate Mode (Nano Banana Pro)", styles['SubHeader']))
    elements.append(Paragraph(
        "Generate visual content from your memories using Gemini 3 Pro image generation.",
        styles['OmniBody']
    ))

    img_features = [
        ['Image Features', 'Memory Integration'],
        ['• 8 preset templates\n• Batch generation (1-4 images)\n• 10 aspect ratios\n• 1K/2K/4K resolution',
         '• Select memories as context\n• Search and filter memories\n• Multi-turn refinement\n• Click-to-edit images']
    ]
    img_table = Table(img_features, colWidths=[2.7*inch, 2.7*inch])
    img_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(img_table)

    elements.append(PageBreak())

    # Style Tab - NEW
    elements.append(Paragraph("Style Tab - NEW in v1.13.0", styles['SectionHeader']))
    elements.append(Paragraph(
        "Manage your personal writing style for use with the Response Composer. The Style Tab helps "
        "you build a profile of your communication patterns.",
        styles['OmniBody']
    ))

    for item in [
        "<b>User Messages</b> - Store sample messages that represent your writing style",
        "<b>Style Markers</b> - Define specific patterns, phrases, and characteristics of your voice",
        "<b>Style Profile</b> - Auto-computed profile based on your samples",
        "<b>Platform Grouping</b> - Organize samples by platform (Skool, email, DM, etc.)",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    # Review Tab
    elements.append(Paragraph("Review Tab (Freshness Management)", styles['SectionHeader']))
    elements.append(Paragraph(
        "Keep your knowledge base fresh by reviewing stale memories.",
        styles['OmniBody']
    ))

    for item in [
        "<b>Days Threshold</b> - Configure: 7, 14, 30, 60, or 90 days",
        "<b>Bulk Selection</b> - Select all or individual memories",
        "<b>Batch Actions</b> - Mark Fresh | Mark Outdated | Archive",
        "<b>Progress Bar</b> - Shows review completion percentage",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    # Graph Tab
    elements.append(Paragraph("Relationship Graph Tab", styles['SectionHeader']))
    elements.append(Paragraph(
        "Interactive D3.js force-directed network visualization of memory connections.",
        styles['OmniBody']
    ))

    graph_data = [
        ['Node Features', 'Edge Types'],
        ['• Color-coded by memory type\n• Drag to reposition\n• Click to select\n• Double-click to recenter',
         '• related_to (solid)\n• supersedes (dashed, amber)\n• derived_from (dotted, purple)\n• contradicts (dotted, red)']
    ]
    graph_table = Table(graph_data, colWidths=[2.7*inch, 2.7*inch])
    graph_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(graph_table)

    elements.append(PageBreak())

    # Header Navigation
    elements.append(Paragraph("Header Navigation", styles['SectionHeader']))

    header_data = [
        ['Element', 'Function'],
        ['Project Switcher', 'Switch between projects; click Manage for full control'],
        ['Multi-Project Selector', 'Select multiple projects to aggregate data (v1.10.0+)'],
        ['Search Bar', 'Full-text search (Enter to search, Esc to clear)'],
        ['Refresh Button', 'Reload data with loading spinner'],
        ['Export Button', 'Export to JSON, Markdown, or CSV'],
        ['Filter Toggle', 'Show/hide the filter panel'],
        ['Theme Switcher', 'Light, Dark, or System preference'],
        ['Help Button', 'Open help modal with shortcuts and tour replay'],
        ['Connection Status', 'Live indicator with auto-updating timer (pulsing dot)'],
    ]
    elements.append(create_table(header_data, [1.8*inch, 3.7*inch]))

    # Multi-Project Features
    elements.append(Paragraph("Multi-Project Features (v1.10.0+)", styles['SubHeader']))
    for item in [
        "<b>Aggregate Statistics</b> - View combined stats across selected projects",
        "<b>Duplication Warning Banner</b> - Alerts when Global Index + individual projects selected",
        "<b>Quick Actions</b> - 'View Global Only' and 'View Projects Only' buttons",
        "<b>Click-to-Toggle</b> - Easy project selection with checkboxes",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    # Keyboard Shortcuts
    elements.append(Paragraph("Keyboard Shortcuts", styles['SectionHeader']))

    shortcuts_data = [
        ['Shortcut', 'Action'],
        ['/', 'Focus search bar'],
        ['Esc', 'Clear selection/filters'],
        ['j / k', 'Navigate down/up through memories'],
        ['Enter', 'Select first memory / Submit chat'],
        ['r', 'Refresh data'],
        ['?', 'Open Help dialog'],
        ['1-9', 'Quick filter by memory type'],
    ]
    elements.append(create_table(shortcuts_data, [1.5*inch, 4*inch]))

    # Pro Tips
    elements.append(Paragraph("Pro Tips", styles['SectionHeader']))
    for item in [
        "First-time users see an <b>onboarding tour</b> - replay it via Help button",
        "Use the <b>Activity Heatmap</b> to identify your most productive periods",
        "Link related memories to build a knowledge graph for visualization",
        "Review stale memories monthly to keep your knowledge base fresh",
        "Use <b>semantic search</b> for conceptual queries (requires omni-cortex[semantic])",
        "Export memories before major refactoring for backup",
        "<b>Star your most-used projects</b> for quick access in the Project Switcher",
        "Use <b>Response Composer</b> to generate style-matched responses for community engagement",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    elements.append(Spacer(1, 20))
    elements.append(create_callout_box(
        "OmniCortex | github.com/AllCytes/Omni-Cortex",
        styles, ACCENT
    ))

    # Build PDF
    def add_header_footer(canvas, doc):
        header_footer(canvas, doc, "Dashboard User Guide")

    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print(f"Created: {filename}")


# ============================================================================
# 2. FEATURE COMPARISON PDF
# ============================================================================

def create_feature_comparison():
    """Create the updated Feature Comparison PDF"""
    styles = get_styles()
    filename = os.path.join(OUTPUT_DIR, 'OmniCortex_FeatureComparison.pdf')

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=50, bottomMargin=50
    )

    elements = []

    # Title
    elements.append(Paragraph("OmniCortex Feature Comparison", styles['DocTitle']))
    elements.append(Paragraph("vs Basic MCP Memory", styles['DocSubtitle']))

    elements.append(Paragraph(
        "OmniCortex provides a comprehensive memory system that goes far beyond basic MCP memory "
        "tools. Here's how they compare:",
        styles['OmniBody']
    ))

    # Feature Comparison Table
    elements.append(Paragraph("Feature Comparison", styles['SectionHeader']))

    comparison_data = [
        ['Feature', 'Basic MCP', 'OmniCortex'],
        ['Memory Storage', 'Simple key-value', 'SQLite with full schema'],
        ['Search', 'Basic lookup', 'Full-text search (FTS5)'],
        ['Memory Types', 'None', '11 types (fact, decision, solution, etc.)'],
        ['Status Tracking', 'None', '4 statuses with freshness management'],
        ['Importance Scoring', 'None', '1-100 scale with filtering'],
        ['Tagging', 'None', 'Multi-tag with search'],
        ['Relationships', 'None', '4 relationship types with graph viz'],
        ['Activity Logging', 'None', 'Complete audit trail'],
        ['Session Management', 'None', 'Full context preservation'],
        ['Cross-Project Search', 'None', 'Global index'],
        ['Multi-Project View', 'None', 'Aggregate data across projects'],
        ['Project Management', 'None', 'Favorites, custom scan dirs, registration'],
        ['Web Dashboard', 'None', 'Full-featured Vue 3 dashboard'],
        ['Export Options', 'None', 'JSON, Markdown, CSV, SQLite'],
        ['Semantic Search', 'None', 'Optional embeddings support'],
        ['Image Generation', 'None', 'Nano Banana Pro integration'],
        ['Response Composer', 'None', 'Style-matched response generation'],
        ['Style Profiles', 'None', 'Personal writing style learning'],
        ['Command Analytics', 'None', 'Slash command/skill usage tracking'],
        ['Security Hardening', 'None', 'XSS/CSRF protection, CSP headers'],
    ]

    elements.append(create_table(comparison_data, [1.8*inch, 1.5*inch, 2.2*inch]))

    elements.append(PageBreak())

    # Key Differentiators
    elements.append(Paragraph("Key Differentiators", styles['SectionHeader']))

    elements.append(Paragraph("Knowledge Graph", styles['SubHeader']))
    elements.append(Paragraph(
        "OmniCortex allows you to link memories together with typed relationships (related_to, supersedes, "
        "derived_from, contradicts), creating a navigable knowledge graph visualized in the dashboard.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Response Composer (NEW in v1.13.0)", styles['SubHeader']))
    elements.append(Paragraph(
        "Generate AI-powered responses that match your personal writing style. Supports platform-aware "
        "formatting (Skool, email, DM, comments), tone adjustment, and uses your stored writing samples "
        "to maintain voice consistency. Enhanced in v1.14.0 with custom instructions and 'Explain to Me' mode.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Style Profile System", styles['SubHeader']))
    elements.append(Paragraph(
        "Build a profile of your communication patterns by storing sample messages. The system learns "
        "your voice, phrases, and style markers to generate responses that sound authentically like you.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Project Management", styles['SubHeader']))
    elements.append(Paragraph(
        "Easily manage multiple projects with configurable scan directories, manual project registration, "
        "and favorites for quick access. All settings persist in ~/.omni-cortex/projects.json.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Freshness Management", styles['SubHeader']))
    elements.append(Paragraph(
        "Memories have status tracking (fresh, needs_review, outdated, archived) with configurable staleness "
        "thresholds. The Review tab helps you maintain knowledge quality over time.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Complete Audit Trail", styles['SubHeader']))
    elements.append(Paragraph(
        "Every tool call is logged with input, output, timing, and success status. The Activity tab provides "
        "full visibility into what Claude has done during your sessions.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Cross-Project Search", styles['SubHeader']))
    elements.append(Paragraph(
        "The global index at ~/.omni-cortex/global.db enables searching across all your projects. Find "
        "patterns and solutions from previous projects instantly.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Image Generation (Nano Banana Pro)", styles['SubHeader']))
    elements.append(Paragraph(
        "Generate visual content directly from your memories using Gemini 3 Pro. Create infographics, "
        "workflow diagrams, quote cards, and more with 8 preset templates and full customization.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Command & Skill Analytics", styles['SubHeader']))
    elements.append(Paragraph(
        "Track which slash commands and skills you use most, with scope differentiation (universal vs project). "
        "Monitor MCP server integration metrics and view success rates for all tool calls.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Security Hardening", styles['SubHeader']))
    elements.append(Paragraph(
        "Production-ready security with XSS protection (DOMPurify), path traversal prevention, security "
        "headers (CSP, X-Frame-Options), and prompt injection protection for LLM integrations.",
        styles['OmniBody']
    ))

    # When to Use What
    elements.append(Paragraph("When to Use What", styles['SectionHeader']))

    use_data = [
        ['Scenario', 'Recommendation'],
        ['Simple note-taking', 'Basic MCP may suffice'],
        ['Project-specific knowledge', 'OmniCortex (project DB)'],
        ['Cross-project patterns', 'OmniCortex (global search)'],
        ['Team knowledge base', 'OmniCortex (export & share)'],
        ['Long-running projects', 'OmniCortex (freshness management)'],
        ['Complex codebases', 'OmniCortex (relationships + graph)'],
        ['Community engagement', 'OmniCortex (Response Composer)'],
        ['Consistent voice across platforms', 'OmniCortex (Style Profiles)'],
    ]
    elements.append(create_table(use_data, [2.5*inch, 3*inch]))

    elements.append(Spacer(1, 20))
    elements.append(create_callout_box(
        "OmniCortex | github.com/AllCytes/Omni-Cortex",
        styles, ACCENT
    ))

    # Build PDF
    def add_header_footer(canvas, doc):
        header_footer(canvas, doc, "Feature Comparison")

    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print(f"Created: {filename}")


# ============================================================================
# 3. STORAGE ARCHITECTURE PDF
# ============================================================================

def create_storage_architecture():
    """Create the updated Storage Architecture PDF"""
    styles = get_styles()
    filename = os.path.join(OUTPUT_DIR, 'OmniCortex_StorageArchitecture.pdf')

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=50, bottomMargin=50
    )

    elements = []

    # Title
    elements.append(Paragraph("OmniCortex Storage Architecture", styles['DocTitle']))
    elements.append(Paragraph("Technical Reference", styles['DocSubtitle']))

    elements.append(Paragraph(
        "OmniCortex uses SQLite for all data storage - a deliberate architectural choice that prioritizes "
        "simplicity, portability, and reliability over distributed complexity.",
        styles['OmniBody']
    ))

    # Why SQLite
    elements.append(Paragraph("Why SQLite?", styles['SectionHeader']))

    why_data = [
        ['Technical Benefits', 'Practical Benefits'],
        ['• Zero configuration required\n• Single-file databases\n• ACID compliant\n• Built-in FTS5 for search',
         '• Works offline\n• Easy backup (copy file)\n• No server process\n• Cross-platform portable']
    ]
    why_table = Table(why_data, colWidths=[2.7*inch, 2.7*inch])
    why_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(why_table)

    # Storage Locations
    elements.append(Paragraph("Storage Locations", styles['SectionHeader']))

    locations_data = [
        ['Location', 'Path', 'Purpose'],
        ['Project DB', '.omni-cortex/cortex.db', 'Memories, activities, sessions for project'],
        ['Global DB', '~/.omni-cortex/global.db', 'Cross-project search index'],
        ['Project Config', '~/.omni-cortex/projects.json', 'Dashboard settings, favorites, scan dirs'],
    ]
    elements.append(create_table(locations_data, [1.2*inch, 2.2*inch, 2.1*inch]))

    # Database Schema
    elements.append(Paragraph("Database Schema", styles['SectionHeader']))

    # memories table
    elements.append(Paragraph("memories Table", styles['SubHeader']))
    memories_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'ULID-based unique identifier'],
        ['content', 'TEXT', 'Main memory content'],
        ['context', 'TEXT', 'Additional context'],
        ['memory_type', 'TEXT', 'fact, decision, solution, etc.'],
        ['status', 'TEXT', 'fresh, needs_review, outdated, archived'],
        ['importance_score', 'INTEGER', '1-100 importance rating'],
        ['tags', 'TEXT', 'JSON array of tags'],
        ['created_at', 'TIMESTAMP', 'Creation time'],
        ['last_accessed', 'TIMESTAMP', 'Last access time'],
        ['access_count', 'INTEGER', 'Number of accesses'],
    ]
    elements.append(create_table(memories_data, [1.5*inch, 1.2*inch, 2.8*inch]))

    # activities table
    elements.append(Paragraph("activities Table", styles['SubHeader']))
    activities_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'ULID-based unique identifier'],
        ['event_type', 'TEXT', 'pre_tool_use, post_tool_use, etc.'],
        ['tool_name', 'TEXT', 'Name of tool called'],
        ['tool_input', 'TEXT', 'JSON input parameters'],
        ['tool_output', 'TEXT', 'JSON output result'],
        ['success', 'BOOLEAN', 'Whether operation succeeded'],
        ['duration_ms', 'INTEGER', 'Execution time in ms'],
        ['session_id', 'TEXT', 'FK to sessions table'],
        ['timestamp', 'TIMESTAMP', 'Event time'],
        ['command_name', 'TEXT', 'Slash command name (v1.3.0+)'],
        ['command_scope', 'TEXT', 'universal or project (v1.3.0+)'],
        ['mcp_server', 'TEXT', 'MCP server name (v1.3.0+)'],
        ['skill_name', 'TEXT', 'Skill name if applicable (v1.3.0+)'],
    ]
    elements.append(create_table(activities_data, [1.5*inch, 1.2*inch, 2.8*inch]))

    elements.append(PageBreak())

    # memory_relationships table
    elements.append(Paragraph("memory_relationships Table", styles['SubHeader']))
    relationships_data = [
        ['Column', 'Type', 'Description'],
        ['source_id', 'TEXT FK', 'Source memory ID'],
        ['target_id', 'TEXT FK', 'Target memory ID'],
        ['relationship_type', 'TEXT', 'related_to, supersedes, derived_from, contradicts'],
        ['strength', 'REAL', 'Relationship strength 0.0-1.0'],
        ['created_at', 'TIMESTAMP', 'When relationship was created'],
    ]
    elements.append(create_table(relationships_data, [1.5*inch, 1.2*inch, 2.8*inch]))

    # sessions table
    elements.append(Paragraph("sessions Table", styles['SubHeader']))
    sessions_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'Session identifier'],
        ['started_at', 'TIMESTAMP', 'Session start time'],
        ['ended_at', 'TIMESTAMP', 'Session end time (nullable)'],
        ['summary', 'TEXT', 'Auto-generated or manual summary'],
        ['key_learnings', 'TEXT', 'JSON array of learnings'],
    ]
    elements.append(create_table(sessions_data, [1.5*inch, 1.2*inch, 2.8*inch]))

    # style_markers table - NEW
    elements.append(Paragraph("style_markers Table (v1.13.0+)", styles['SubHeader']))
    style_markers_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'Marker identifier'],
        ['marker_type', 'TEXT', 'phrase, pattern, characteristic'],
        ['content', 'TEXT', 'The style marker content'],
        ['platform', 'TEXT', 'Associated platform (optional)'],
        ['created_at', 'TIMESTAMP', 'Creation time'],
    ]
    elements.append(create_table(style_markers_data, [1.5*inch, 1.2*inch, 2.8*inch]))

    # user_messages table - NEW
    elements.append(Paragraph("user_messages Table (v1.13.0+)", styles['SubHeader']))
    user_messages_data = [
        ['Column', 'Type', 'Description'],
        ['id', 'TEXT PK', 'Message identifier'],
        ['content', 'TEXT', 'The message content'],
        ['platform', 'TEXT', 'Platform context (skool, email, dm, etc.)'],
        ['context_type', 'TEXT', 'Type of communication'],
        ['created_at', 'TIMESTAMP', 'When message was stored'],
    ]
    elements.append(create_table(user_messages_data, [1.5*inch, 1.2*inch, 2.8*inch]))

    # FTS5
    elements.append(Paragraph("Full-Text Search (FTS5)", styles['SectionHeader']))
    elements.append(Paragraph(
        "OmniCortex uses SQLite's FTS5 extension for fast full-text search across memory content and context.",
        styles['OmniBody']
    ))
    elements.append(create_callout_box(
        "FTS5 Index: memories_fts (content, context)<br/>"
        "Supports: phrase matching, prefix search, boolean operators",
        styles, SECONDARY
    ))

    # Global Index
    elements.append(Paragraph("Global Index", styles['SectionHeader']))
    elements.append(Paragraph(
        "The global database at ~/.omni-cortex/global.db maintains a cross-project search index for "
        "finding memories across all your projects.",
        styles['OmniBody']
    ))

    global_data = [
        ['Column', 'Type', 'Description'],
        ['memory_id', 'TEXT', 'Original memory ID'],
        ['project_path', 'TEXT', 'Source project path'],
        ['content', 'TEXT', 'Memory content (synced)'],
        ['memory_type', 'TEXT', 'Memory type'],
        ['tags', 'TEXT', 'JSON tags array'],
        ['synced_at', 'TIMESTAMP', 'Last sync time'],
    ]
    elements.append(create_table(global_data, [1.5*inch, 1.2*inch, 2.8*inch]))

    elements.append(PageBreak())

    # Project Configuration
    elements.append(Paragraph("Project Configuration", styles['SectionHeader']))
    elements.append(Paragraph(
        "Dashboard project preferences are stored in ~/.omni-cortex/projects.json:",
        styles['OmniBody']
    ))

    config_data = [
        ['Field', 'Type', 'Description'],
        ['version', 'integer', 'Config schema version'],
        ['scan_directories', 'string[]', 'Directories to scan for projects'],
        ['registered_projects', 'object[]', 'Manually added projects with path, display_name, added_at'],
        ['favorites', 'string[]', 'Paths of favorite projects'],
        ['recent', 'object[]', 'Recently accessed projects (last 10) with path, last_accessed'],
    ]
    elements.append(create_table(config_data, [1.8*inch, 1.2*inch, 2.5*inch]))

    # Backup & Migration
    elements.append(Paragraph("Backup & Migration", styles['SectionHeader']))
    elements.append(Paragraph(
        "Because OmniCortex uses file-based storage, backup and migration are straightforward:",
        styles['OmniBody']
    ))

    for item in [
        "<b>Project Backup:</b> Copy the .omni-cortex/ directory",
        "<b>Global Backup:</b> Copy ~/.omni-cortex/ directory",
        "<b>Migration:</b> Move directories to new machine - no reconfiguration needed",
        "<b>Export:</b> Use cortex_export tool for JSON/Markdown/SQLite exports",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    elements.append(Spacer(1, 20))
    elements.append(create_callout_box(
        "OmniCortex | github.com/AllCytes/Omni-Cortex",
        styles, ACCENT
    ))

    # Build PDF
    def add_header_footer(canvas, doc):
        header_footer(canvas, doc, "Storage Architecture")

    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print(f"Created: {filename}")


# ============================================================================
# 4. QUICK START PDF
# ============================================================================

def create_quick_start():
    """Create the updated Quick Start PDF"""
    styles = get_styles()
    filename = os.path.join(OUTPUT_DIR, 'OmniCortex_QuickStart.pdf')

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=50, bottomMargin=50
    )

    elements = []

    # Title
    elements.append(Paragraph("OmniCortex Quick Start", styles['DocTitle']))
    elements.append(Paragraph("Get Started in 5 Minutes", styles['DocSubtitle']))

    elements.append(Paragraph(
        "OmniCortex gives Claude persistent memory across sessions. This guide will have you up and "
        "running in minutes.",
        styles['OmniBody']
    ))

    # 1. Installation
    elements.append(Paragraph("1. Installation", styles['SectionHeader']))
    elements.append(create_callout_box("pip install omni-cortex", styles, ACCENT))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Or with optional features:", styles['OmniBody']))
    elements.append(create_callout_box(
        "pip install omni-cortex[semantic]  # Semantic search<br/>"
        "pip install omni-cortex[all]       # All features",
        styles, SECONDARY
    ))

    # 2. Configure
    elements.append(Paragraph("2. Configure Claude Code", styles['SectionHeader']))
    elements.append(Paragraph(
        "Add OmniCortex to your Claude Code MCP configuration:",
        styles['OmniBody']
    ))
    elements.append(Paragraph("~/.claude/claude_desktop_config.json:", styles['OmniBody']))

    config_text = '''{
  "mcpServers": {
    "omni-cortex": {
      "command": "omni-cortex",
      "args": ["serve"]
    }
  }
}'''
    elements.append(Paragraph(f"<pre>{config_text}</pre>", styles['CodeBlock']))

    # 3. First Use
    elements.append(Paragraph("3. First Use", styles['SectionHeader']))
    elements.append(Paragraph(
        "Start Claude Code in any project directory. OmniCortex will automatically:",
        styles['OmniBody']
    ))
    for item in [
        "Create .omni-cortex/ directory in your project",
        "Initialize cortex.db SQLite database",
        "Make memory tools available to Claude",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    # 4. Core Tools
    elements.append(Paragraph("4. Core Tools", styles['SectionHeader']))
    tools_data = [
        ['Tool', 'Purpose', 'Example'],
        ['cortex_remember', 'Store information', 'Store this API pattern'],
        ['cortex_recall', 'Search memories', 'Find auth-related memories'],
        ['cortex_list_memories', 'Browse all', 'Show recent decisions'],
        ['cortex_update_memory', 'Modify memory', 'Add tags to memory'],
        ['cortex_link_memories', 'Create relations', 'Link related solutions'],
    ]
    elements.append(create_table(tools_data, [1.5*inch, 1.3*inch, 2.2*inch]))

    # 5. Web Dashboard
    elements.append(Paragraph("5. Web Dashboard", styles['SectionHeader']))
    elements.append(create_callout_box("omni-cortex-dashboard", styles, ACCENT))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Opens a visual interface at http://localhost:8765 for browsing memories, viewing activity logs, "
        "and analyzing your knowledge base. Includes <b>Response Composer</b> for generating style-matched "
        "responses to community messages.",
        styles['OmniBody']
    ))

    elements.append(PageBreak())

    # 6. Storage Locations
    elements.append(Paragraph("6. Storage Locations", styles['SectionHeader']))
    storage_data = [
        ['Location', 'Path', 'Purpose'],
        ['Project DB', '.omni-cortex/cortex.db', 'Project memories & activities'],
        ['Global DB', '~/.omni-cortex/global.db', 'Cross-project search index'],
        ['Project Config', '~/.omni-cortex/projects.json', 'Dashboard settings & favorites'],
    ]
    elements.append(create_table(storage_data, [1.2*inch, 2.2*inch, 2.1*inch]))

    # 7. Memory Types
    elements.append(Paragraph("7. Memory Types", styles['SectionHeader']))
    types_data = [
        ['Type', 'Use For'],
        ['fact', 'Technical facts, API details, configurations'],
        ['decision', 'Architectural choices, design decisions'],
        ['solution', 'Working fixes, implementation patterns'],
        ['error', 'Error resolutions, debugging insights'],
        ['progress', 'Current state, work in progress'],
        ['preference', 'User preferences, coding style choices'],
    ]
    elements.append(create_table(types_data, [1.5*inch, 4*inch]))

    # 8. Pro Tips
    elements.append(Paragraph("8. Pro Tips", styles['SectionHeader']))
    for item in [
        'Ask Claude to "remember this" when you solve a tricky problem',
        "Use tags liberally - they're searchable and filterable",
        "Link related memories to build a knowledge graph",
        "Review stale memories periodically (use the Review tab)",
        "Export memories before major refactoring",
        "Use the global index for cross-project patterns",
        "Try <b>Response Composer</b> to generate replies that match your writing style",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    # Next Steps
    elements.append(Paragraph("Next Steps", styles['SectionHeader']))
    elements.append(Paragraph("Now that you're set up, explore these resources:", styles['OmniBody']))
    for item in [
        "<b>Command Reference</b> - Full tool documentation",
        "<b>Dashboard Guide</b> - Visual interface walkthrough",
        "<b>Storage Architecture</b> - Technical deep dive",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    elements.append(Spacer(1, 20))
    elements.append(create_callout_box(
        "OmniCortex | github.com/AllCytes/Omni-Cortex",
        styles, ACCENT
    ))

    # Build PDF
    def add_header_footer(canvas, doc):
        header_footer(canvas, doc, "Quick Start Guide")

    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print(f"Created: {filename}")


# ============================================================================
# 5. TROUBLESHOOTING FAQ PDF
# ============================================================================

def create_troubleshooting_faq():
    """Create the updated Troubleshooting FAQ PDF"""
    styles = get_styles()
    filename = os.path.join(OUTPUT_DIR, 'OmniCortex_TroubleshootingFAQ.pdf')

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=50, bottomMargin=50
    )

    elements = []

    # Title
    elements.append(Paragraph("OmniCortex Troubleshooting", styles['DocTitle']))
    elements.append(Paragraph("FAQ & Common Issues", styles['DocSubtitle']))

    # Installation Issues
    elements.append(Paragraph("Installation Issues", styles['SectionHeader']))

    elements.append(Paragraph("Q: pip install fails with dependency errors", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Try installing with the --upgrade flag to ensure latest versions:",
        styles['OmniBody']
    ))
    elements.append(create_callout_box("pip install --upgrade omni-cortex", styles, ACCENT))

    elements.append(Paragraph("Q: Command 'omni-cortex' not found after install", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Ensure your Python scripts directory is in PATH. On Windows, try:",
        styles['OmniBody']
    ))
    elements.append(create_callout_box("python -m omni_cortex serve", styles, SECONDARY))

    # Connection Issues
    elements.append(Paragraph("Connection Issues", styles['SectionHeader']))

    elements.append(Paragraph("Q: Claude can't see OmniCortex tools", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Check your MCP configuration is correct. Verify the server is running:",
        styles['OmniBody']
    ))
    elements.append(create_callout_box("omni-cortex serve --debug", styles, SECONDARY))

    elements.append(Paragraph("Q: Dashboard shows 'Connection Lost'", styles['SubHeader']))
    elements.append(Paragraph(
        "A: The WebSocket connection may have timed out. Click Refresh or restart the dashboard.",
        styles['OmniBody']
    ))

    # Data Issues
    elements.append(Paragraph("Data Issues", styles['SectionHeader']))

    elements.append(Paragraph("Q: Where is my data stored?", styles['SubHeader']))
    data_locations = [
        ['Data Type', 'Location'],
        ['Project memories', '.omni-cortex/cortex.db (in project)'],
        ['Global index', '~/.omni-cortex/global.db'],
        ['Dashboard config', '~/.omni-cortex/projects.json'],
    ]
    elements.append(create_table(data_locations, [1.8*inch, 3.7*inch]))

    elements.append(Paragraph("Q: How do I backup my memories?", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Simply copy the .omni-cortex/ directory. It's a self-contained SQLite database.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Q: Can I reset/delete all memories?", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Delete the .omni-cortex/cortex.db file. A new one will be created on next use.",
        styles['OmniBody']
    ))

    elements.append(PageBreak())

    # Dashboard Issues
    elements.append(Paragraph("Dashboard Issues", styles['SectionHeader']))

    elements.append(Paragraph("Q: Dashboard won't start", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Check if port 8765 is available. Try a different port:",
        styles['OmniBody']
    ))
    elements.append(create_callout_box("omni-cortex-dashboard --port 8080", styles, SECONDARY))

    elements.append(Paragraph("Q: Projects not showing in Project Switcher", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Ensure your project directories are in the scan list. Open Project Management (Manage button) "
        "and add your directory under the Directories tab, or manually register the project under Add Project.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Q: Ask AI tab shows 'API key not configured'", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Set your Gemini API key as an environment variable:",
        styles['OmniBody']
    ))
    elements.append(create_callout_box("export GEMINI_API_KEY=your_api_key_here", styles, ACCENT))

    # Response Composer Issues - NEW
    elements.append(Paragraph("Response Composer Issues (v1.13.0+)", styles['SectionHeader']))

    elements.append(Paragraph("Q: Response Composer generates generic responses", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Add more sample messages to your style profile. Go to the Style tab and store examples "
        "of your actual writing. The more samples, the better the style matching.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Q: 'Explain to Me' mode not showing explanation", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Ensure you've checked the 'Explain message to me first' checkbox before generating. "
        "The explanation appears in a blue card above the generated response.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Q: Custom instructions not reflected in response", styles['SubHeader']))
    elements.append(Paragraph(
        "A: Make sure your custom instructions are specific. Vague instructions may be interpreted "
        "differently. Try being more explicit about what you want included.",
        styles['OmniBody']
    ))

    # Performance Issues
    elements.append(Paragraph("Performance Issues", styles['SectionHeader']))

    elements.append(Paragraph("Q: Search is slow with many memories", styles['SubHeader']))
    elements.append(Paragraph(
        "A: OmniCortex uses FTS5 indexing which should handle 10,000+ memories efficiently. If you're "
        "experiencing slowness, try running VACUUM on the database.",
        styles['OmniBody']
    ))

    elements.append(Paragraph("Q: Dashboard is laggy with large datasets", styles['SubHeader']))
    elements.append(Paragraph(
        "A: The dashboard uses infinite scroll and lazy loading. Try filtering to reduce the result set, "
        "or use the search to narrow down results.",
        styles['OmniBody']
    ))

    # Getting Help
    elements.append(Paragraph("Getting Help", styles['SectionHeader']))
    elements.append(Paragraph("If your issue isn't covered here:", styles['OmniBody']))
    for item in [
        "Check the GitHub Issues for similar problems",
        "Run with --debug flag for detailed logging",
        "Open a new issue with reproduction steps",
    ]:
        elements.append(Paragraph(f"• {item}", styles['BulletItem']))

    elements.append(Spacer(1, 20))
    elements.append(create_callout_box(
        "OmniCortex | github.com/AllCytes/Omni-Cortex",
        styles, ACCENT
    ))

    # Build PDF
    def add_header_footer(canvas, doc):
        header_footer(canvas, doc, "Troubleshooting FAQ")

    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print(f"Created: {filename}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Generate all updated PDFs"""
    print("Updating OmniCortex PDF Documentation...")
    print(f"Output directory: {OUTPUT_DIR}")
    print("-" * 50)

    create_dashboard_guide()
    create_feature_comparison()
    create_storage_architecture()
    create_quick_start()
    create_troubleshooting_faq()

    print("-" * 50)
    print("All PDFs updated successfully!")


if __name__ == "__main__":
    main()
