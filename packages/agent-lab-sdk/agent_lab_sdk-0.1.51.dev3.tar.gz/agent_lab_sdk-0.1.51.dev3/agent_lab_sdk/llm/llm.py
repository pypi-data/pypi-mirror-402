from langchain_gigachat.chat_models import GigaChat
from langchain_gigachat.embeddings import GigaChatEmbeddings
from agent_lab_sdk.llm.gigachat_token_manager import GigaChatTokenManager
from agent_lab_sdk.llm.token_manager_utils import build_token_manager_kwargs
from agent_lab_sdk.llm.throttled import ThrottledGigaChat, ThrottledGigaChatEmbeddings
from typing import Union
import os

def get_model(
    type: str = "chat",
    throttled: bool = True,
    manage_access_token: bool = True,
    **kwargs
) -> Union[
    GigaChat,
    GigaChatEmbeddings,
    ThrottledGigaChat,
    ThrottledGigaChatEmbeddings,
]:
    """
    * type - определяет тип моледи : chat | embeddings
    * throttled - оборачивает модель в класс обертку с дополнительным регулированием через семафор
    * manage_access_token - включает режим авто-обновления токена в обёртках (только если throttled=True)
    * retry - включает retry-поведение (только если throttled=True)
    * kwargs - прокидываются в модель
    """
    access_token = kwargs.pop("access_token", None)
    retry_attempts_count = kwargs.pop("retry_attempts_count", None)
    retry_config = kwargs.pop("retry_config", None)
    retry = kwargs.pop("retry", False)
    use_retry = throttled and retry
    token_manager_kwargs = build_token_manager_kwargs(
        kwargs,
        kwargs.pop("token_manager_kwargs", None),
    )
    if not access_token:
        user = kwargs.get("user", None)
        password = kwargs.get("password", None)
        if not user and not password and not (throttled and manage_access_token):
            access_token = GigaChatTokenManager.get_token(**token_manager_kwargs)

    verify_ssl_certs = kwargs.pop("verify_ssl_certs", False)
    verify_ssl_certs = os.getenv("GIGACHAT_VERIFY_SSL_CERTS", verify_ssl_certs)

    if type == "chat":
        _class = ThrottledGigaChat if throttled else GigaChat
    elif type == "embeddings":
        _class = ThrottledGigaChatEmbeddings if throttled else GigaChatEmbeddings
    else:
        raise ValueError(f"unsupported type {type}. possible values: chat, embeddings")

    if throttled and manage_access_token:
        # Включаем режим авто-обновления токена в обёртках
        kwargs["manage_access_token"] = True
        kwargs["token_manager_kwargs"] = token_manager_kwargs
    if throttled:
        if use_retry:
            if retry_config is None:
                if retry_attempts_count is None:
                    retry_attempts_count = 3
                retry_config = {"retry_attempts_count": retry_attempts_count}
            kwargs["retry_config"] = retry_config
            kwargs["retry"] = True

    if access_token:
        kwargs["access_token"] = access_token

    return _class(verify_ssl_certs=verify_ssl_certs, **kwargs)
