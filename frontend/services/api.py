"""
APIクライアント
バックエンドへのすべてのHTTPリクエストをここに集約する
"""

import requests
import os
from typing import Optional

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
TIMEOUT_SHORT = 5
TIMEOUT_NORMAL = 10
TIMEOUT_AI = 60


# ===== 物件 =====

def get_properties(params: dict = {}) -> list:
    resp = requests.get(f"{BACKEND_URL}/api/properties", params=params, timeout=TIMEOUT_NORMAL)
    resp.raise_for_status()
    return resp.json()


def get_property_stats() -> list:
    resp = requests.get(f"{BACKEND_URL}/api/properties/stats", timeout=TIMEOUT_SHORT)
    resp.raise_for_status()
    return resp.json()


# ===== 活用診断 =====

def run_diagnosis(property_id: int) -> dict:
    resp = requests.post(f"{BACKEND_URL}/api/diagnosis/{property_id}", timeout=TIMEOUT_AI)
    resp.raise_for_status()
    return resp.json()


# ===== 移住サポート =====

def get_regions(params: dict = {}) -> dict:
    resp = requests.get(f"{BACKEND_URL}/api/migration/regions", params=params, timeout=TIMEOUT_NORMAL)
    resp.raise_for_status()
    return resp.json()


def compare_regions(prefectures: str) -> dict:
    resp = requests.get(
        f"{BACKEND_URL}/api/migration/compare",
        params={"prefectures": prefectures},
        timeout=TIMEOUT_NORMAL
    )
    resp.raise_for_status()
    return resp.json()


def migration_chat(question: str, prefecture: Optional[str] = None) -> dict:
    payload = {"question": question}
    if prefecture:
        payload["prefecture"] = prefecture
    resp = requests.post(f"{BACKEND_URL}/api/migration/chat", json=payload, timeout=TIMEOUT_AI)
    resp.raise_for_status()
    return resp.json()


# ===== DIYサポート =====

def get_diy_categories() -> dict:
    resp = requests.get(f"{BACKEND_URL}/api/diy/categories", timeout=TIMEOUT_SHORT)
    resp.raise_for_status()
    return resp.json()


def get_diy_advice(payload: dict) -> dict:
    resp = requests.post(f"{BACKEND_URL}/api/diy/advice", json=payload, timeout=TIMEOUT_AI)
    resp.raise_for_status()
    return resp.json()


def get_diy_checklist(payload: dict) -> dict:
    resp = requests.post(f"{BACKEND_URL}/api/diy/checklist", json=payload, timeout=TIMEOUT_AI)
    resp.raise_for_status()
    return resp.json()


# ===== メンター =====

def match_mentors(payload: dict) -> dict:
    resp = requests.post(f"{BACKEND_URL}/api/mentors/match", json=payload, timeout=TIMEOUT_AI)
    resp.raise_for_status()
    return resp.json()


def get_mentors(params: dict = {}) -> dict:
    resp = requests.get(f"{BACKEND_URL}/api/mentors", params=params, timeout=TIMEOUT_NORMAL)
    resp.raise_for_status()
    return resp.json()


def send_consultation(payload: dict) -> dict:
    resp = requests.post(f"{BACKEND_URL}/api/mentors/request", json=payload, timeout=TIMEOUT_NORMAL)
    resp.raise_for_status()
    return resp.json()


# ===== チャット =====

def chat(question: str, domain: Optional[str] = None) -> dict:
    payload = {"question": question}
    if domain:
        payload["domain"] = domain
    resp = requests.post(f"{BACKEND_URL}/api/chat", json=payload, timeout=TIMEOUT_AI)
    resp.raise_for_status()
    return resp.json()


def get_chat_stats() -> dict:
    resp = requests.get(f"{BACKEND_URL}/api/chat/stats", timeout=TIMEOUT_SHORT)
    resp.raise_for_status()
    return resp.json()