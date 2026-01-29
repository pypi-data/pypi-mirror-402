from typing import Any, Dict, Optional

_TOKEN_MANAGER_PARAM_KEYS = (
    "credentials",
    "user",
    "password",
    "scope",
    "auth_url",
    "base_url",
)
_TOKEN_MANAGER_EXTRA_KEYS = (
    "use_gigachat_advanced",
    "use_token_provider_agw",
    "token_file_path",
)


def build_token_manager_kwargs(
    kwargs: dict,
    overrides: Optional[dict] = None,
) -> Dict[str, Any]:
    token_kwargs: Dict[str, Any] = {}
    for key in _TOKEN_MANAGER_PARAM_KEYS:
        if key in kwargs and kwargs[key] is not None:
            token_kwargs[key] = kwargs[key]
    for key in _TOKEN_MANAGER_EXTRA_KEYS:
        if key in kwargs:
            token_kwargs[key] = kwargs.pop(key)
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                token_kwargs[key] = value
    return token_kwargs


__all__ = ["build_token_manager_kwargs"]
