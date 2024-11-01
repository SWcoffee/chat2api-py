import json
import os

import ua_generator
import random

from utils.Logger import logger
from utils.config import proxy_url_list

DATA_FOLDER = "data"
TOKENS_FILE = os.path.join(DATA_FOLDER, "token.txt")
REFRESH_MAP_FILE = os.path.join(DATA_FOLDER, "refresh_map.json")
ERROR_TOKENS_FILE = os.path.join(DATA_FOLDER, "error_token.txt")
WSS_MAP_FILE = os.path.join(DATA_FOLDER, "wss_map.json")
USER_AGENTS_FILE = os.path.join(DATA_FOLDER, "user_agents.json")

count = 0
token_list = []
error_token_list = []
refresh_map = {}
wss_map = {}
user_agent_map = {}
impersonate_list = [
    "chrome99",
    "chrome100",
    "chrome101",
    "chrome104",
    "chrome107",
    "chrome110",
    "chrome116",
    "chrome119",
    "chrome120",
    "chrome123",
    "edge99",
    "edge101",
]

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

if os.path.exists(REFRESH_MAP_FILE):
    with open(REFRESH_MAP_FILE, "r") as file:
        refresh_map = json.load(file)
else:
    refresh_map = {}

if os.path.exists(WSS_MAP_FILE):
    with open(WSS_MAP_FILE, "r") as file:
        wss_map = json.load(file)
else:
    wss_map = {}


if os.path.exists(TOKENS_FILE):
    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                token_list.append(line.strip())
else:
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        pass


if os.path.exists(ERROR_TOKENS_FILE):
    with open(ERROR_TOKENS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                error_token_list.append(line.strip())
else:
    with open(ERROR_TOKENS_FILE, "w", encoding="utf-8") as f:
        pass

if os.path.exists(USER_AGENTS_FILE):
    with open(USER_AGENTS_FILE, "r", encoding="utf-8") as f:
        try:
            user_agent_map = json.load(f)
        except json.JSONDecodeError:
            user_agent_map = {}
    # 对比token_list和user_agent_map，如果token_list中有而user_agent_map中没有，则生成新的ua
    new_tokens = list(set(token_list) - user_agent_map.keys())
    for token in new_tokens:
        ua = ua_generator.generate(device='desktop', browser=('chrome', 'edge'), platform=('windows', 'macos'))
        ua_dict = {
            "user-agent": ua.text,
            "sec-ch-ua-platform": ua.platform,
            "sec-ch-ua": ua.ch.brands,
            "sec-ch-ua-mobile": ua.ch.mobile,
            "impersonate": random.choice(impersonate_list),
            "proxy_url": random.choice(proxy_url_list) if proxy_url_list else None,
        }
        user_agent_map[token] = ua_dict
    # 更新proxy_url
    # 检查所有的ua是否有proxy_url是否存在于proxy_url_list中，如果不存在则重新生成
    for token, ua_dict in user_agent_map.items():
        if "proxy_url" in ua_dict and ua_dict["proxy_url"] not in proxy_url_list:
            ua_dict["proxy_url"] = random.choice(proxy_url_list) if proxy_url_list else None
    with open(USER_AGENTS_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(user_agent_map, indent=4))
else:
    for token in token_list:
        ua = ua_generator.generate(device='desktop', browser=('chrome', 'edge'), platform=('windows', 'macos'))
        ua_dict = {
            "user-agent": ua.text,
            "sec-ch-ua-platform": ua.platform,
            "sec-ch-ua": ua.ch.brands,
            "sec-ch-ua-mobile": ua.ch.mobile,
            "impersonate": random.choice(impersonate_list),
            "proxy_url": random.choice(proxy_url_list) if proxy_url_list else None,
        }
        user_agent_map[token] = ua_dict
    with open(USER_AGENTS_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(user_agent_map, indent=4))

if token_list:
    logger.info(f"Token list count: {len(token_list)}, Error token list count: {len(error_token_list)}")
