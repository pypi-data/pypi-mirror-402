import json
import os
from typing import Dict, Optional


def get_connection_as_json(conn_id: str) -> str:
    # Сначала пытаемся получить секрет из переменных окружения
    secret = os.environ.get(conn_id)

    if not secret:
        # Если нет в переменных окружения, пробуем получить из Vault
        try:
            # Попытка импорта vault_client (если доступен)
            from mnemosyne.vault.client import VaultClient

            # Создаем клиент Vault
            vault_client = VaultClient()

            # Получаем секрет из Vault
            secret = vault_client.get_secret(conn_id)

            if not secret:
                raise ValueError(f"Секрет {conn_id} не найден ни в переменных окружения, ни в Vault")

        except ImportError:
            # Если Vault клиент недоступен, бросаем исключение
            raise ValueError(f"Секрет {conn_id} не найден в переменных окружения и не удалось подключиться к Vault")
        except Exception as e:
            raise ValueError(f"Ошибка при получении секрета {conn_id} из Vault: {str(e)}")

    return secret


def get_secret(conn_id: str) -> Dict:
    raw = get_connection_as_json(conn_id)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Секрет {conn_id} не является корректным JSON: {e}")

def get_connection_as_json_test(conn_id: str, dir_path: str = "./secrets") -> str:
    """
    Возвращает JSON-конфиг подключения для тестов.
    Вместо Vault берёт локальный JSON-файл из dir_path.
    Файл должен называться <conn_id>.json
    """
    file_path = os.path.join(dir_path, f"{conn_id}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Тестовый секрет {file_path} не найден")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def get_secret_test(conn_id: str, dir_path: str = "./secrets") -> Dict:
    """
    Возвращает словарь конфигурации для тестов.
    Читает локальный JSON вместо Vault.
    """
    raw = get_connection_as_json_test(conn_id, dir_path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Тестовый секрет {conn_id} не является корректным JSON: {e}")
