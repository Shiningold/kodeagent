"""异常体系。"""


class KodeAgentError(Exception):
    """框架基础异常。"""


class KLMError(KodeAgentError):
    """LLM 相关错误的基类。"""


class AuthError(KLMError):
    """API Key 失效或未配置。不重试，提示用户更新 .env。"""


class ProviderError(KLMError):
    """LLM Provider 调用失败（网络 / 服务端错误）。"""


class ToolError(KodeAgentError):
    """工具执行错误。"""


class BlockedError(KodeAgentError):
    """工具调用被 hook 阻断。"""
