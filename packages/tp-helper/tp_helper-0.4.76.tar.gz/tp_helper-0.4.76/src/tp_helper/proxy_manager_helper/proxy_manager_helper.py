import aiohttp
from pydantic import ValidationError

from tp_helper.proxy_manager_helper.schemas.proxy_schema import ProxySchema


class ProxyManagerHelper:
    def __init__(self, proxy_manager_url: str):
        self.proxy_manager_url = proxy_manager_url.rstrip("/")
        self.proxy_schema: ProxySchema | None = None


    async def get_one_proxy(self, queue: str) -> ProxySchema:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.proxy_manager_url}/proxies",
                params={"queue": queue},
            ) as response:
                text = await response.text()

                # 1. Проверяем статус ответа
                if response.status != 200:
                    raise RuntimeError(
                        f"Proxy Manager вернул статус {response.status}: {text}"
                    )

                # 2. Пытаемся распарсить JSON
                try:
                    data = await response.json()
                except Exception as e:
                    raise RuntimeError(
                        f"Proxy Manager вернул ответ, который не является корректным JSON: {text}"
                    ) from e

                # 3. Проверяем, что это не null
                if data is None:
                    raise RuntimeError(
                        f"Proxy Manager вернул null для очереди queue={queue} "
                        f"(возможно, нет доступных прокси)"
                    )

                # 4. Валидируем через Pydantic
                try:
                    self.proxy_schema = ProxySchema.model_validate(data)
                except ValidationError as e:
                    raise RuntimeError(
                        f"Proxy Manager вернул некорректные данные прокси: {data}"
                    ) from e

                return self.proxy_schema

    async def get_proxy_url(self, queue: str) -> str:
        await self.get_one_proxy(queue=queue)
        return self.get_http()

    def get_http(self) -> str:
        if self.proxy_schema is None:
            raise RuntimeError("Proxy not loaded. Call get_one_proxy first.")
        return (
            f"http://{self.proxy_schema.login}:"
            f"{self.proxy_schema.password}@"
            f"{self.proxy_schema.ip}:"
            f"{self.proxy_schema.port}"
        )

