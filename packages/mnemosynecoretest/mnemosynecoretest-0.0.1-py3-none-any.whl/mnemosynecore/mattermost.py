import logging
import json
from typing import Optional, Union
from mattermostdriver import Driver
from mnemosynecore.vault import get_secret
from sqlalchemy import create_engine
from .vault import get_secret_test


def get_mattermost_driver_test(bot_id: str, dir_path: str = "./secrets") -> Driver:
    """
    Возвращает Mattermost Driver для тестов.
    Использует JSON-файл вместо Vault.
    """
    cfg = get_secret_test(bot_id, dir_path)

    driver = Driver({
        "url": cfg["host"],
        "token": cfg["password"],
        "schema": cfg.get("schema", "https"),
        "port": int(cfg.get("port", 443)),
        "basepath": cfg.get("basepath", "/api/v4"),
    })

    driver.login()
    return driver


def send_message_test(
    *,
    channel_id: str,
    bot_id: str,
    text: str,
    dir_path: str = "./secrets",
    silent: bool = False,
) -> None:
    """
    Отправляет сообщение в Mattermost от имени бота для тестов.
    Использует локальный JSON вместо Vault.
    """
    driver = get_mattermost_driver_test(bot_id, dir_path)

    try:
        driver.posts.create_post(
            options={
                "channel_id": channel_id,
                "message": text.strip(),
            }
        )
        if not silent:
            print(f"[TEST] Сообщение отправлено в Mattermost: {channel_id}")
    except Exception as exc:
        print(f"[TEST] Ошибка отправки сообщения: {exc}")
        raise


def get_mattermost_driver(bot_id: str) -> Driver:
    """
    Создаёт и логинит Mattermost Driver через Vault.
    """
    # Проверяем, является ли bot_id строкой JSON
    if bot_id.startswith('{'):
        try:
            cfg = json.loads(bot_id)
        except json.JSONDecodeError:
            raise ValueError("Неверный формат JSON для конфигурации Mattermost")
    else:
        # Используем старый способ - получаем из Vault
        cfg = get_secret(bot_id)

    driver = Driver({
        "url": cfg["host"],
        "token": cfg["password"],
        "schema": cfg.get("schema", "https"),
        "port": int(cfg.get("port", 443)),
        "basepath": cfg.get("basepath", "/api/v4"),
    })

    driver.login()
    return driver

def get_mattermost_conn(conn_id: str) -> dict:
    """
    Получает параметры подключения к Mattermost из Vault
    """
    cfg_json = json.loads(get_connection_as_json(conn_id))

    return {
        "host": cfg_json.get("host"),
        "password": cfg_json.get("password"),
        "schema": cfg_json.get("schema", "https"),
        "port": int(cfg_json.get("port", 443)),
        "basepath": json.loads(cfg_json.get("extra", "{}")).get(
            "basepath", "/api/v4"
        ),
    }


def get_connection_as_json(conn_name):
    import json
    from airflow.hooks.base import BaseHook

    conn = BaseHook.get_connection(conn_name)
    ci = {'host': conn.host, 'password': conn.password, 'login': conn.login, 'port': conn.port, 'schema': conn.schema,
          'extra': conn.extra}
    return json.dumps(ci)


def send_message(
    *,
    channel_id: str,
    bot_id: str,
    text: str,
    silent: bool = False,
) -> None:
    """
    Отправляет сообщение в Mattermost от имени бота.

    :param channel_id: ID канала
    :param bot_id: ID секрета в Vault или JSON-строка конфигурации
    :param text: Markdown-текст сообщения
    :param silent: не логировать успешную отправку
    """
    driver = get_mattermost_driver(bot_id)

    try:
        driver.posts.create_post(
            options={
                "channel_id": channel_id,
                "message": text.strip(),
            }
        )
        if not silent:
            logging.info("Сообщение отправлено в Mattermost: %s", channel_id)

    except Exception as exc:
        logging.exception(
            "Ошибка отправки сообщения в Mattermost (channel_id=%s)",
            channel_id
        )
        raise