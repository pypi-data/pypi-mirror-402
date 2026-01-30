"""
MBM Constants

Central location for all application-wide constants, banners, and
static configuration values.
"""

from typing import Final

# Application metadata
APP_NAME: Final[str] = "MBM"
APP_VERSION: Final[str] = "0.1.0"
APP_DESCRIPTION: Final[str] = "Modular CLI Platform with Aaryan Language & AI Assistant"
APP_AUTHOR: Final[str] = "MBM Team"
APP_URL: Final[str] = "https://github.com/mbm/mbm-cli"

# File extensions
AARYAN_FILE_EXTENSION: Final[str] = ".ar"

# API endpoints (legal, public sources only)
WIKIPEDIA_API_URL: Final[str] = "https://en.wikipedia.org/api/rest_v1/page/summary"
WIKIMEDIA_COMMONS_API: Final[str] = "https://commons.wikimedia.org/w/api.php"

# Request configuration
DEFAULT_TIMEOUT: Final[int] = 10
MAX_RETRIES: Final[int] = 3
USER_AGENT: Final[str] = f"MBM-CLI/{APP_VERSION} (Educational; +{APP_URL})"

# NLP configuration
SPACY_MODEL: Final[str] = "en_core_web_sm"

# Intent types
INTENT_IMAGE: Final[str] = "image"
INTENT_INFO: Final[str] = "info"
INTENT_UNKNOWN: Final[str] = "unknown"

# ASCII Art Banner
BANNER: Final[str] = r"""
███╗   ███╗██████╗ ███╗   ███╗
████╗ ████║██╔══██╗████╗ ████║
██╔████╔██║██████╔╝██╔████╔██║
██║╚██╔╝██║██╔══██╗██║╚██╔╝██║
██║ ╚═╝ ██║██████╔╝██║ ╚═╝ ██║
╚═╝     ╚═╝╚═════╝ ╚═╝     ╚═╝
"""

BANNER_SUBTITLE: Final[str] = "Modular CLI Platform | Aaryan Language | AI Assistant"

# Help text
HELP_TEXT: Final[str] = """
╭─────────────────────────────────────────────────────────────╮
│                    MBM CLI Platform                         │
├─────────────────────────────────────────────────────────────┤
│  USAGE:                                                     │
│    mbm                     Show this help                   │
│    mbm aaryan              Aaryan language module           │
│    mbm aaryan run <file>   Run an Aaryan program            │
│    mbm ai                  Start AI assistant               │
│    mbm <person>            View person's profile            │
│                                                             │
│  EXAMPLES:                                                  │
│    mbm aaryan run hello.ar                                  │
│    mbm ai                                                   │
│    mbm preeti                                               │
│                                                             │
│  For more info: mbm --help                                  │
╰─────────────────────────────────────────────────────────────╯
"""

# Color scheme (Rich library colors)
COLORS: Final[dict] = {
    "primary": "bright_cyan",
    "secondary": "bright_magenta",
    "success": "bright_green",
    "warning": "bright_yellow",
    "error": "bright_red",
    "info": "bright_blue",
    "muted": "dim white",
    "highlight": "bold bright_white",
}

# Exit codes
EXIT_SUCCESS: Final[int] = 0
EXIT_ERROR: Final[int] = 1
EXIT_USAGE_ERROR: Final[int] = 2
EXIT_FILE_NOT_FOUND: Final[int] = 3
EXIT_RUNTIME_ERROR: Final[int] = 4
