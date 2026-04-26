# Domain constants: regex patterns, thresholds, keyword lists
import re

CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")
URL_PATTERN = re.compile(r"https?://[^\s\)\"\']+")
