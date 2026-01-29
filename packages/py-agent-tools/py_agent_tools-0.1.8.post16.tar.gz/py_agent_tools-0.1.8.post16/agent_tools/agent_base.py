import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable

from pydantic_ai import Agent, BinaryContent
from pydantic_ai.exceptions import AgentRunError, ModelHTTPError, UserError
from pydantic_ai.models.openai import Model
from pydantic_ai.settings import ModelSettings

from agent_tools._log import log
from agent_tools.agent_factory import AgentFactory
from agent_tools.agent_runner import AgentRunner
from agent_tools.credential_pool_base import CredentialPoolProtocol, ModelCredential, StatusType
from agent_tools.wechat_alert import agent_exception_handler


class ModelNameBase(str, Enum):
    """
    表示已测试的模型名称。
    """

    pass


class AgentBase(ABC):
    """Base class for all agents.

    Args:
        credential or credential_pool: Exactly one of credential or credential_pool
            must be provided.
        system_prompt: The system prompt to use for the agent.
        max_retries: The maximum number of retries to make when the agent fails.
        model_settings: The model settings to use for the agent.
    """

    def __init__(
        self,
        credential: ModelCredential | None = None,
        credential_pool: CredentialPoolProtocol | None = None,
        system_prompt: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        model_settings: ModelSettings = ModelSettings(),
    ):
        if (credential is None) == (credential_pool is None):
            raise ValueError("Exactly one of credential or credential_pool must be None")

        self.credential = credential
        self.credential_pool = credential_pool
        self.timeout = timeout
        self.max_retries = max_retries
        self._initial_retries = max_retries  # 保存初始重试次数
        self.system_prompt: str | None = system_prompt
        self.runner = AgentRunner(
            model_settings=model_settings,
        )

    @classmethod
    async def create(
        cls,
        credential: ModelCredential | None = None,
        credential_pool: CredentialPoolProtocol | None = None,
        system_prompt: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        model_settings: ModelSettings | None = None,
    ) -> "AgentBase":
        if model_settings is None:
            model_settings = ModelSettings(temperature=0.0)
        instance = cls(
            credential,
            credential_pool,
            system_prompt,
            timeout,
            max_retries,
            model_settings,
        )
        await instance._initialize_credential(credential, credential_pool)
        return instance

    def _update_model_settings(self):
        if self.credential is None:
            raise ValueError("Credential is not initialized!")
        if len(self.credential.model_settings.keys()) > 0:
            for k, v in self.credential.model_settings.items():
                if v is None and self.runner.model_settings.get(k) is not None:
                    log.warning(f"Delete '{k}' from model settings")
                    self.runner.model_settings.pop(k, None)  # type: ignore
                else:
                    if v != self.runner.model_settings.get(k):
                        log.info(f"Update '{k}' from {self.runner.model_settings.get(k)} to {v}")
                        self.runner.model_settings[k] = v  # type: ignore
            log.info(f"Model settings in agent: {self.runner.model_settings}")

    async def _initialize_credential(
        self,
        credential: ModelCredential | None,
        credential_pool: CredentialPoolProtocol | None,
    ):
        if credential_pool is not None:
            if len(credential_pool.get_model_credentials()) == 0:
                raise ValueError("Credential pool is empty")
            elif len(credential_pool.get_model_credentials()) == 1:
                self.credential = credential_pool.get_model_credentials()[0]
                self.credential_pool = None
            else:
                self.credential_pool = credential_pool
                self.credential = await credential_pool.get_best()
        elif credential is not None:
            self.credential = credential
            self.credential_pool = None
        else:
            raise ValueError("Either credential or credential_pool must be provided")
        self._update_model_settings()

    async def _switch_credential(self):
        from agent_tools._log import log

        if self.credential_pool is not None and self.credential is not None:
            await self.credential_pool.update_status(self.credential, StatusType.ERROR)
            self.credential = await self.credential_pool.get_best()
        else:
            log.info(f"等待重试 - Agent: {self.__class__.__name__}, 等待1秒后重试...")
            await asyncio.sleep(1)

        self.max_retries -= 1
        log.info(
            f"重试计数更新 - Agent: {self.__class__.__name__}, " f"剩余重试次数: {self.max_retries}"
        )

        if self.max_retries <= 0:
            # 重新抛出最后一个异常，让装饰器能够捕获
            if hasattr(self, '_last_exception'):
                raise self._last_exception
            else:
                raise ValueError("Max retries reached")
        self._update_model_settings()

    @abstractmethod
    def create_client(self) -> Any:
        """Create a client for the agent by self.credential"""
        pass

    @abstractmethod
    def create_model(self) -> Model:
        """Create a model for the agent according to model provider"""
        pass

    def create_agent(self) -> Agent[Any, str]:
        """Default agent creation function"""
        model = self.create_model()
        return AgentFactory.create_agent(
            model,
            system_prompt=self.system_prompt,
        )

    @agent_exception_handler()
    async def validate_credential(self) -> bool:
        agent = self.create_agent()
        try:
            await self.runner.run(agent, 'this is a test, just echo "hello"', stream=True)
            return True
        except (ModelHTTPError, AgentRunError, UserError):
            raise
        except Exception:
            return False

    @agent_exception_handler()
    async def run(
        self,
        prompt: str,
        images: list[BinaryContent] = [],
        postprocess_fn: Callable[[str], Any] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> AgentRunner:
        """Run with retries"""
        agent = self.create_agent()
        try:
            await self.runner.run(
                agent, prompt, images=images, postprocess_fn=postprocess_fn, stream=stream, **kwargs
            )
        except (ModelHTTPError, AgentRunError, UserError):
            # pydantic_ai的异常，直接重新抛出，让装饰器处理
            raise
        except Exception as e:
            if self.max_retries <= 0:
                from agent_tools._log import log

                log.error(f"重试次数已用完，最终失败: {type(e).__name__}: {e}")
                raise e

            self._last_exception = e

            # 记录准备重试的日志
            from agent_tools._log import log

            initial_retries = getattr(self, '_initial_retries', self.max_retries + 1)
            current_retry = initial_retries - self.max_retries
            total_retries = initial_retries - 1
            log.info(
                f"🔄 准备重试 - Agent: {self.__class__.__name__}, "
                f"异常: {type(e).__name__}, "
                f"即将进行第 {current_retry + 1}/{total_retries + 1} 次重试, "
                f"剩余重试次数: {self.max_retries}, "
                f"错误信息: {str(e)[:100]}{'...' if len(str(e)) > 100 else ''}"
            )

            await self._switch_credential()
            # 设置重试标志，避免装饰器重复记录异常
            self._in_retry = True
            try:
                return await self.run(
                    prompt, images=images, postprocess_fn=postprocess_fn, stream=stream, **kwargs
                )
            finally:
                # 清除重试标志
                if hasattr(self, '_in_retry'):
                    delattr(self, '_in_retry')
        return self.runner

    @agent_exception_handler()
    async def embedding(
        self,
        input: str,
        dimensions: int = 1024,
    ) -> AgentRunner | None:
        """Embedding with retries"""
        if self.credential is None:
            raise ValueError("Credential is not initialized")
        if 'embedding' not in self.credential.model_name:
            raise ValueError("Model is not an embedding model, use run instead")
        try:
            await self.runner.embedding(
                self.create_client(),
                self.credential.model_name,
                input,
                dimensions,
            )
        except (ModelHTTPError, AgentRunError, UserError):
            raise
        except Exception as e:
            # 保存最后一个异常
            self._last_exception = e
            await self._switch_credential()
            # 设置重试标志，避免装饰器重复记录异常
            self._in_retry = True
            try:
                return await self.embedding(input, dimensions)
            finally:
                # 清除重试标志
                if hasattr(self, '_in_retry'):
                    delattr(self, '_in_retry')
        return self.runner
