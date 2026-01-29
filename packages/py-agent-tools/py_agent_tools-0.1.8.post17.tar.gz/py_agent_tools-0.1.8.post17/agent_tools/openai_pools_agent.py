from openai import AsyncOpenAI
from pydantic_ai.exceptions import AgentRunError, ModelHTTPError, UserError
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from agent_tools.agent_base import AgentBase, ModelNameBase
from agent_tools.credential_pool_base import (
    CredentialPoolBase,
    CredentialPoolProtocol,
    ModelCredential,
)
from agent_tools.provider_config import AccountCredential
from agent_tools.wechat_alert import agent_exception_handler


class OpenAIPoolsModelName(ModelNameBase):
    GPT_4O = "gpt-4o"
    O4_MINI = "o4-mini"
    GPT_5 = "gpt-5"
    GPT_41 = "gpt-4.1"
    GPT_41_MINI = "gpt-4.1-mini"
    GPT_5_MINI = "gpt-5-mini"
    GEMINI_3_FLASH = "gemini-3-flash-preview"
    QWEN3_MAX_PREVIEW = "qwen3-max-preview"
    QWEN3_VL_PLUS = "qwen3-vl-plus"


class OpenAIPoolsAgent(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_source: str | None = getattr(self, "config_source", None)

    def create_client(self) -> AsyncOpenAI:
        if self.credential is None:
            raise ValueError("Credential is not initialized")

        default_headers = {}

        if self.config_source:
            default_headers["X-Config-Source"] = self.config_source

        base_url = self.credential.base_url

        if self.config_source == "bailian":
            base_url = "https://beta-apisix.hgj.com/model-openai-pools/account-pool/v1"

        base_url = base_url.rstrip("/")

        return AsyncOpenAI(
            api_key=self.credential.api_key,
            base_url=base_url,
            timeout=self.timeout,
            default_headers=default_headers,
        )

    def create_model(self) -> OpenAIChatModel:
        if self.credential is None:
            raise ValueError("Credential is not initialized")
        client = self.create_client()
        return OpenAIChatModel(
            model_name=self.credential.model_name,
            provider=OpenAIProvider(openai_client=client),
        )

    def embedding(self, input: str, dimensions: int = 1024):
        raise NotImplementedError("OpenAIPoolsAgent does not support embedding")

    @classmethod
    async def create_with_config_source(
        cls,
        credential: ModelCredential,
        model_settings=None,
        config_source: str | None = None,
    ):
        agent = await cls.create(credential=credential, model_settings=model_settings)
        # 类型检查器需要知道这是一个OpenAIPoolsAgent实例
        if isinstance(agent, OpenAIPoolsAgent):
            agent.config_source = config_source
        return agent

    @agent_exception_handler()
    async def validate_credential(self) -> bool:
        "重写"
        agent = self.create_agent()
        try:
            await self.runner.run(
                agent, 'this is a test, just echo "hello"', stream=False
            )
            return True
        except (ModelHTTPError, AgentRunError, UserError):
            raise
        except Exception:
            return False


async def validate_fn(credential: ModelCredential) -> bool:
    agent = await OpenAIPoolsAgent.create(credential=credential)
    return await agent.validate_credential()


class OpenAIPoolsCredentialPool(CredentialPoolBase):
    def __init__(
        self,
        model_provider: str,
        target_model: OpenAIPoolsModelName,
        account_credentials: list[AccountCredential],
    ):
        super().__init__(
            model_provider=model_provider,
            target_model=target_model,
            account_credentials=account_credentials,
            validate_fn=validate_fn,
        )


async def test_with_config_source(
    credential_pool_cls: type[CredentialPoolProtocol],
    agent_cls: type[OpenAIPoolsAgent],
    model_provider: str,
    target_model: str,
    account_credentials: list[AccountCredential],
    model_settings: OpenAIChatModelSettings,
    config_source: str | None,
    stream: bool = False,
):
    """测试带有config_source的agent功能"""
    from agent_tools._log import log
    from agent_tools.credential_pool_base import LocalCredentialPool

    credential_pool = credential_pool_cls(
        model_provider=model_provider,
        target_model=target_model,
        account_credentials=account_credentials,
    )
    if isinstance(credential_pool, LocalCredentialPool):
        await credential_pool.start()

    # 获取一个可用的凭证
    available_credentials = credential_pool.get_model_credentials()
    if not available_credentials:
        print("没有可用的凭证进行测试")
        return

    credential = available_credentials[0]

    # 使用create_with_config_source方法创建agent
    agent_tool = await agent_cls.create_with_config_source(
        credential=credential,
        model_settings=model_settings,
        config_source=config_source,
    )
    log.info(f"Agent created with config_source: {config_source}")

    runner = await agent_tool.run("100字描述中国", stream=stream)
    print(f"Config Source: {config_source}")
    print(f"Result: {runner.result}")

    if isinstance(credential_pool, LocalCredentialPool):
        credential_pool.stop()


if __name__ == "__main__":
    import asyncio

    from agent_tools.tools4test import test_credential_pool_manager, with_agent_switcher

    model_settings = OpenAIChatModelSettings(
        temperature=0.0,
        max_tokens=8192,
        openai_reasoning_effort="low",
    )
    provider = "openai_pools"
    import time

    @with_agent_switcher(providers=[provider])
    async def test(agent_switcher):
        """主函数，运行所有测试并正确清理资源。"""
        # 测试流式模式
        print("=== 测试流式模式 ===")
        start_time = time.time()
        await test_credential_pool_manager(
            credential_pool_cls=OpenAIPoolsCredentialPool,
            agent_cls=OpenAIPoolsAgent,
            model_provider=provider,
            account_credentials=agent_switcher.provider_mappings[
                provider
            ].account_credentials,
            target_model=OpenAIPoolsModelName.GEMINI_3_FLASH,
            model_settings=model_settings,
            stream=True,  # 流式模式
        )
        print(time.time() - start_time)
        # # 测试非流式模式
        # print("\n=== 测试非流式模式 ===")
        # start_time = time.time()

        # await test_credential_pool_manager(
        #     credential_pool_cls=OpenAIPoolsCredentialPool,
        #     agent_cls=OpenAIPoolsAgent,
        #     model_provider=provider,
        #     account_credentials=agent_switcher.provider_mappings[provider].account_credentials,
        #     target_model=OpenAIPoolsModelName.O4_MINI,
        #     model_settings=model_settings,
        #     stream=False,  # 非流式模式
        # )
        # print(time.time() - start_time)

        # 测试config_source功能
        # print("\n=== 测试config_source功能 ===")
        # test_config_sources = [
        #     'laozhang',
        #     'openai',  # 测试没有config_source的情况
        # ]

        # for config_source in test_config_sources:
        #     print(f"\n--- 测试config_source: {config_source} ---")
        #     await test_with_config_source(
        #         credential_pool_cls=OpenAIPoolsCredentialPool,
        #         agent_cls=OpenAIPoolsAgent,
        #         model_provider=provider,
        #         account_credentials=agent_switcher.provider_mappings[provider].account_credentials,
        #         target_model=OpenAIPoolsModelName.O4_MINI,
        #         model_settings=model_settings,
        #         config_source=config_source,
        #         stream=True,
        #     )

        # # 测试所有凭证
        # print("\n=== 测试所有凭证 ===")
        # await test_all_credentials(
        #     model_name_enum=OpenAIPoolsModelName,
        #     model_settings=model_settings,
        #     credential_pool_cls=OpenAIPoolsCredentialPool,
        #     agent_cls=OpenAIPoolsAgent,
        #     model_provider=provider,
        #     account_credentials=agent_switcher.provider_mappings[provider].account_credentials,
        # )

    try:
        asyncio.run(test())
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            print("测试成功完成（清理警告已忽略）")
        else:
            raise
