"""
Основной клиент для работы с Pollinations AI API
"""

import requests
from typing import Optional, List, Union, Iterator
from urllib.parse import quote

from .models import Message, ChatResponse, Model


class PollinationsClient:
    """
    Простой клиент для Pollinations AI
    
    Примеры использования:
    
    # Быстрый запрос
    >>> client = PollinationsClient()
    >>> response = client.ask("Привет! Как дела?")
    >>> print(response)
    
    # Чат с историей
    >>> response = client.chat([
    ...     Message("system", "Ты полезный ассистент"),
    ...     Message("user", "Расскажи про Python")
    ... ])
    >>> print(response.content)
    
    # С выбором модели
    >>> response = client.ask("Реши задачу", model="gemini")
    """
    
    # API endpoints
    BASE_URL = "https://gen.pollinations.ai"
    TEXT_URL = "https://text.pollinations.ai"
    CHAT_URL = TEXT_URL  # POST endpoint для чата
    OPENAI_CHAT_URL = f"{BASE_URL}/v1/chat/completions"  # Требует API ключ
    MODELS_URL = f"{TEXT_URL}/models"
    
    # Доступные модели
    MODELS = {
        "gemini": "Gemini 2.5 Flash Lite (с поддержкой изображений)",
        "mistral": "Mistral Small 3.2 24B",
        "openai": "GPT-OSS 20B Reasoning LLM",
        "openai-fast": "GPT-OSS 20B Reasoning LLM (алиас)",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openai",
        system_prompt: Optional[str] = None,
        timeout: int = 60,
    ):
        """
        Инициализация клиента
        
        Args:
            api_key: API ключ (опционально, для повышенных лимитов)
            model: Модель по умолчанию
            system_prompt: Системный промпт по умолчанию
            timeout: Таймаут запросов в секундах
        """
        self.api_key = api_key
        self.default_model = model
        self.default_system_prompt = system_prompt
        self.timeout = timeout
        self.retries = 3
        self._session = requests.Session()
        
        if api_key:
            self._session.headers["Authorization"] = f"Bearer {api_key}"

    def _post(self, url: str, json: dict, stream: bool = False):
        """Внутренний метод для POST запросов с повторными попытками"""
        import time
        from requests.exceptions import RequestException
        
        last_error = None
        for attempt in range(self.retries):
            try:
                response = self._session.post(url, json=json, timeout=self.timeout, stream=stream)
                if response.status_code >= 500:
                    response.raise_for_status()
                return response
            except RequestException as e:
                last_error = e
                if attempt < self.retries - 1:
                    time.sleep(1 * (attempt + 1))
                    continue
                raise last_error
        if last_error:
            raise last_error
    
    def ask(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Простой запрос к модели (один вопрос - один ответ)
        
        Args:
            prompt: Ваш вопрос/запрос
            model: Модель (по умолчанию из инициализации)
            system_prompt: Системный промпт
            seed: Сид для воспроизводимости
            json_mode: Режим JSON ответа
            
        Returns:
            Текст ответа
        """
        messages = []
        
        sys = system_prompt or self.default_system_prompt
        if sys:
            messages.append(Message("system", sys))
        
        messages.append(Message("user", prompt))
        
        response = self.chat(
            messages=messages,
            model=model,
            seed=seed,
            json_mode=json_mode,
        )
        
        return response.content
    
    def chat(
        self,
        messages: List[Union[Message, dict]],
        model: Optional[str] = None,
        seed: Optional[int] = None,
        json_mode: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        """
        Чат с историей сообщений
        
        Args:
            messages: Список сообщений (Message или dict)
            model: Модель
            seed: Сид для воспроизводимости
            json_mode: Режим JSON ответа
            temperature: Температура генерации (0-2)
            max_tokens: Максимум токенов в ответе
            
        Returns:
            ChatResponse с ответом
        """
        # Преобразуем сообщения в dict
        msg_list = []
        for m in messages:
            if isinstance(m, Message):
                msg_list.append(m.to_dict())
            elif isinstance(m, dict):
                msg_list.append(m)
            else:
                raise ValueError(f"Неверный тип сообщения: {type(m)}")
        
        # Формируем запрос
        payload = {
            "model": model or self.default_model,
            "messages": msg_list,
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        if temperature is not None:
            payload["temperature"] = temperature
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        # Выбираем endpoint в зависимости от API ключа
        url = self.OPENAI_CHAT_URL if self.api_key else self.CHAT_URL
        
        # Отправляем запрос
        response = self._post(
            url,
            json=payload,
            stream=False
        )
        response.raise_for_status()
        
        # Парсим ответ - разный формат для разных endpoints
        if self.api_key:
            # OpenAI-совместимый формат
            data = response.json()
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            
            return ChatResponse(
                content=message.get("content", ""),
                model=data.get("model", payload["model"]),
                finish_reason=choice.get("finish_reason", "stop"),
                usage=data.get("usage"),
                raw_response=data,
            )
        else:
            # Простой текстовый ответ от text.pollinations.ai
            return ChatResponse(
                content=response.text,
                model=payload["model"],
                finish_reason="stop",
                usage=None,
                raw_response=None,
            )
    
    def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Стриминг ответа (получение по частям)
        
        Args:
            prompt: Ваш запрос
            model: Модель
            system_prompt: Системный промпт
            
        Yields:
            Части текста по мере генерации
        """
        messages = []
        
        sys = system_prompt or self.default_system_prompt
        if sys:
            messages.append({"role": "system", "content": sys})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": True,
        }
        
        url = self.OPENAI_CHAT_URL if self.api_key else self.CHAT_URL
        
        response = self._post(
            url,
            json=payload,
            stream=True,
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        
                        # Собираем контент из разных возможных полей
                        content = delta.get("content", "") or delta.get("reasoning_content", "")
                        
                        if content:
                            yield content
                    except:
                        continue
    
    def quick(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Самый быстрый способ - прямой GET запрос
        
        Args:
            prompt: Ваш запрос
            model: Модель
            
        Returns:
            Текст ответа
        """
        url = f"{self.TEXT_URL}/{quote(prompt)}"
        
        params = {}
        if model:
            params["model"] = model
        if self.default_system_prompt:
            params["system"] = self.default_system_prompt
        
        response = self._session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        return response.text
    
    def get_models(self) -> List[Model]:
        """
        Получить список доступных моделей
        
        Returns:
            Список объектов Model
        """
        response = self._session.get(self.MODELS_URL, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        return [Model.from_dict(m) for m in data]
    
    def __repr__(self) -> str:
        return f"PollinationsClient(model='{self.default_model}')"


# Удобные функции для быстрого использования
_default_client: Optional[PollinationsClient] = None


def _get_client() -> PollinationsClient:
    global _default_client
    if _default_client is None:
        _default_client = PollinationsClient()
    return _default_client


def ask(prompt: str, model: str = "openai", **kwargs) -> str:
    """
    Быстрый запрос без создания клиента
    
    >>> from pollinations import ask
    >>> answer = ask("Что такое Python?")
    """
    client = _get_client()
    return client.ask(prompt, model=model, **kwargs)


def chat(messages: list, model: str = "openai", **kwargs) -> ChatResponse:
    """
    Быстрый чат без создания клиента
    
    >>> from pollinations import chat, Message
    >>> response = chat([Message("user", "Привет!")])
    """
    client = _get_client()
    return client.chat(messages, model=model, **kwargs)
