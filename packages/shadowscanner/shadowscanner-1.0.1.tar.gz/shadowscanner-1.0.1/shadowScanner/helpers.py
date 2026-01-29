import json
import sys
import threading
import time
import logging
import shadowScanner.globals as GLOBALS

def split_hackerone_key(key: str):
    return key.split(":") if ":" in key else (key, "")

# I found myself spending too much time on logging which is dumb
# So i decided to just stop and continue with what i have.
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[95m',  
        'INFO': '\033[96m',   
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',  
        'CRITICAL': '\033[41m',
        'RESET': '\033[0m', 
    }

    def format(self, record):
        log_message = super().format(record)
        color_code = self.COLORS.get(record.levelname, self.COLORS['RESET'])

        if record.levelname in ("INFO", "WARNING"):
            prefix = "[!]"
        elif record.levelname in ("DEBUG", "CRITICAL"):
            prefix = "[+]"
        else:
            prefix = "[X]"

        return f"{color_code}{prefix} {log_message}{self.COLORS['RESET']}"


def configure_logging(verbosity_level):
    if not verbosity_level:
        log_level = logging.WARNING
    elif verbosity_level == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    logger = logging.getLogger()
    logger.setLevel(log_level)

    colored_handler = logging.StreamHandler(sys.stdout)

    formatter = ColoredFormatter("%(message)s")
    colored_handler.setFormatter(formatter)

    logger.addHandler(colored_handler)


class Spinner:
    def __init__(self, message):
        self.message = message
        self.done = False
        self.frames = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
        self.thread = None

    def start(self):
        def spin():
            self.hide_cursor()
            try:
                i = 0
                num_frames = len(self.frames)
                while not self.done:
                    sys.stdout.write("\r\033[2K")
                    sys.stdout.write(f"\033[36m{self.frames[i]}\033[0m {self.message}")
                    sys.stdout.flush()
                    i = (i + 1) % num_frames
                    time.sleep(0.05)
            finally:
                self.show_cursor()
                sys.stdout.write("\r\033[2K")
                sys.stdout.flush()

        self.thread = threading.Thread(target=spin, daemon=True)
        self.thread.start()
        return self


    def updateMessage(self, message):
        self.message = message

    def hide_cursor(self):
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    def show_cursor(self):
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


    __enter__ = start

    def stop(self):
        self.done = True
        if self.thread:
            self.thread.join()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def create_cache_if_not_created():
    if not GLOBALS.CACHE_FILE.is_file():
        logging.info(f"[!] Cache file doesn't exist. Creating cache file at {GLOBALS.CACHE_FILE}")
        GLOBALS.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        GLOBALS.CACHE_FILE.touch()

def store_in_cache(key: str, value):
    create_cache_if_not_created()

    with open(GLOBALS.CACHE_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    data[key] = value

    with open(GLOBALS.CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_from_cache(key: str):
    create_cache_if_not_created()

    with open(GLOBALS.CACHE_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    return data.get(key)
    

def add_https_prefix(url):
    return f"https://{url}" if not url.startswith("http") else url


# def fetch_javascript_content(self, url: str, js_url: str) -> Optional[str]:
#     try:
#         full_url = urljoin(url, js_url)
#         response = self.session.get(full_url, timeout=15, verify=True)
#         if response.status_code == 200:
#             return response.text
#     except Exception as e:
#         if self.verbose:
#             logger.warning(f"Failed to fetch JS from {js_url}: {e}")
#     return None


# def is_custom_javascript(self, js_content: str, js_url: str) -> Tuple[bool, str]:
    #     if not js_content:
    #         return False, "No content"

    #     indicators = {"npm_package": 0, "custom": 0}

    #     npm_patterns = [
    #         r"node_modules",
    #         r"/*!.*?https?://npmjs\.com",
    #         r"@license",
    #         r"webpack://",
    #         r"//# sourceMappingURL=.*node_modules",
    #         r"typeof exports.*typeof module",
    #         r"__webpack_require__",
    #         r"__esModule",
    #     ]

    #     for pattern in npm_patterns:
    #         if re.search(pattern, js_content[:5000], re.IGNORECASE):
    #             indicators["npm_package"] += 1

    #     custom_patterns = [
    #         r"function\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*\(",
    #         r"const\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*=",
    #         r"let\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*=",
    #         r"class\s+[a-zA-Z_$][a-zA-Z0-9_$]*",
    #     ]

    #     for pattern in custom_patterns:
    #         matches = re.findall(pattern, js_content[:10000])
    #         if len(matches) > 5:
    #             indicators["custom"] += 1

    #     parsed_url = urlparse(js_url)
    #     path = parsed_url.path.lower()

    #     if any(
    #         marker in path for marker in ["bundle", "app", "main", "custom", "script"]
    #     ):
    #         indicators["custom"] += 2

    #     if any(
    #         marker in path
    #         for marker in [
    #             "vendor",
    #             "lib",
    #             "framework",
    #             "jquery",
    #             "lodash",
    #             "react",
    #             "vue",
    #             "angular",
    #         ]
    #     ):
    #         indicators["npm_package"] += 2

    #     if indicators["custom"] > indicators["npm_package"]:
    #         return (
    #             True,
    #             f"custom:{indicators['custom']},npm:{indicators['npm_package']}",
    #         )
    #     elif indicators["npm_package"] > indicators["custom"]:
    #         return (
    #             False,
    #             f"custom:{indicators['custom']},npm:{indicators['npm_package']}",
    #         )
    #     else:
    #         return False, "unclear"