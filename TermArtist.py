class TermArtist:
    """
    A class containing different colors 
    and methods for printing to terminal.
    """
    
    DIMYELLOW = "\033[33m"
    WHITE = '\033[37m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MEGANTA = '\033[95m'
    CYAN = '\033[96m'
    ERROR = RED
    RESET = '\033[0m'
    ENDC = RESET
    "Reset"
    BOLD = '\033[1m'
    FAINT = '\033[2m'
    "Dim, decrease density"
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    SLOWBLINK = '\033[5m'
    RAPIDBLINK = '\033[6m'
    "MS-DOS ANSI.SYS, 150+ per minute; not widely supported"
    NOBLINK = '\033[25m'
    "Turn off blinking"
    CONCEAL = '\033[8m'
    "Not widely supported."
    CROSSOUT = '\033[9m'
    "Characters legible but marked as if for deletion. Not supported in Terminal.app"
    DEBUG = "\x1b[0;30;43m"
    "Combined syntax (Black Font, Yellow BG)"