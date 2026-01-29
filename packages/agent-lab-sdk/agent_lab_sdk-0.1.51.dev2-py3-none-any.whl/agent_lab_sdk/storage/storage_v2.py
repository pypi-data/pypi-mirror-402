import os
from typing import Optional
import logging
import requests
from urllib.parse import urljoin
from pydantic import BaseModel
import httpx

logger = logging.getLogger(__name__)


class FileUploadResponse(BaseModel):
    """Ответ от сервиса загрузки файлов"""
    id: Optional[str] = None
    bucket: Optional[str] = None
    key: Optional[str] = None
    storage: Optional[str] = None
    absolute_path: str



def _get_upload_path(root: str):
    return urljoin(root, "files/v2/upload")

def upload_file(filename: str, file_bytes: bytes) -> Optional[FileUploadResponse]:
    """
    Загружает файл в бинарном формате через v2 API и возвращает информацию о загруженном файле.

    Args:
        filename: имя файла
        file_bytes: содержимое файла в виде байтов

    Returns:
        FileUploadResponse с информацией о файле или None в случае ошибки
    """

    ai_agent = os.getenv("AGENT_SERVICE_NAME")
    if not ai_agent:
        raise ValueError("AGENT_SERVICE_NAME environment variable is required")

    gateway_url = os.getenv("STORAGE_PROVIDER_AGW_URL", "http://localhost")
    url = _get_upload_path(gateway_url)

    headers = {
        "x-agent-id": ai_agent,
        "Content-Type": "application/octet-stream"
    }

    params = {
        "name": filename
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=file_bytes
        )
        response.raise_for_status()

        if response.status_code == 200:
            data = response.json()
            return FileUploadResponse(
                id=data.get("id", ""),
                bucket=data.get("bucket", ""),
                key=data.get("key", ""),
                storage=data.get("storage", ""),
                absolute_path=data.get("absolutePath", "")
            )

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке файла через v2 API: {e}")

    return None


async def async_upload_file(filename: str, file_bytes: bytes, timeout=30.) -> Optional[FileUploadResponse]:
    """
    Асинхронная версия upload_file

    Args:
        filename: имя файла
        file_bytes: содержимое файла в виде байтов

    Returns:
        FileUploadResponse с информацией о файле или None в случае ошибки
    """

    ai_agent = os.getenv("AGENT_SERVICE_NAME")
    if not ai_agent:
        raise ValueError("AGENT_SERVICE_NAME environment variable is required")

    gateway_url = os.getenv("STORAGE_PROVIDER_AGW_URL", "http://localhost")
    url = _get_upload_path(gateway_url)

    headers = {"x-agent-id": ai_agent, "Content-Type": "application/octet-stream"}
    params = {"name": filename}

    logger.debug(
        f"V2 upload request, filename: {filename}, size: {len(file_bytes)}, url: {url}, agent-id: {ai_agent}"
    )
    try:
        async with httpx.AsyncClient(verify=False, trust_env=True) as client:
            response = await client.post(
                url=url,
                headers=headers,
                params=params,
                content=file_bytes,
                timeout=timeout,
            )
            response.raise_for_status()

            data = response.json()
            return FileUploadResponse(
                id=data.get("id", ""),
                bucket=data.get("bucket", ""),
                key=data.get("key", ""),
                storage=data.get("storage", ""),
                absolute_path=data.get("absolutePath", ""),
            )

    except httpx.HTTPStatusError as err:
        try:
            error_text = err.response.text
        except httpx.StreamError:
            error_text = "empty_stream"
        logger.error(f"HTTP Status Error: {err.response.status_code} - {error_text}")
    except httpx.HTTPError as err:
        logger.error(f"Unable to upload filename: {filename} because of {err}")
        logger.exception(f"Upload error: {err}, filename: {filename}")
    return None
