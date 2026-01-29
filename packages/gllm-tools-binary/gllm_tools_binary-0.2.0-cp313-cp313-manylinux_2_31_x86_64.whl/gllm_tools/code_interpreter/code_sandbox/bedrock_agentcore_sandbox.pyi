import aioboto3
from _typeshed import Incomplete
from gllm_inference.schema import Attachment as Attachment
from gllm_tools.code_interpreter.code_sandbox.constants import Language as Language
from gllm_tools.code_interpreter.code_sandbox.models import ExecutionResult as ExecutionResult, ExecutionStatus as ExecutionStatus
from gllm_tools.code_interpreter.code_sandbox.sandbox import BaseSandbox as BaseSandbox
from gllm_tools.code_interpreter.code_sandbox.utils import calculate_duration_ms as calculate_duration_ms
from typing import Any

logger: Incomplete

class BedrockAgentCoreSandbox(BaseSandbox):
    """AWS Bedrock AgentCore Code Interpreter sandbox implementation.

    This sandbox uses AWS Bedrock AgentCore to execute Python code in a secure,
    managed environment with full async support via aioboto3.

    Attributes:
        region (str): AWS region for Bedrock service.
        aioboto3_session (aioboto3.Session): aioboto3 session with credentials.
        session_timeout (int): Session timeout in seconds (server-side).
        _client: aioboto3 bedrock-agentcore client.
        _client_context: aioboto3 bedrock-agentcore client context.
        _session_id (str | None): Active session ID.
        _is_started (bool): Track if session is started.
    """
    region: str
    aioboto3_session: aioboto3.Session
    session_timeout: int
    def __init__(self, region: str = ..., aws_access_key_id: str | None = None, aws_secret_access_key: str | None = None, language: str = ..., session_timeout: int = ..., aioboto3_session_kwargs: dict[str, Any] | None = None) -> None:
        '''Initialize Bedrock AgentCore sandbox.

        Args:
            region (str): AWS region for Bedrock service. Defaults to "us-east-1".
            aws_access_key_id (str | None): AWS access key. If none, it will use environment variables credentials.
                Defaults to None.
            aws_secret_access_key (str | None): AWS secret key. If none, it will use environment variables credentials.
                Defaults to None.
            language (str): Programming language (currently only "python" supported). Defaults to "python".
            session_timeout (int): Maximum session lifetime in seconds. Defaults to 60.
            aioboto3_session_kwargs (dict[str, Any] | None): Additional aioboto3
                session parameters (e.g., profile_name, botocore_session).

        Raises:
            ValueError: If language is not Python.
        '''
    async def execute_code(self, code: str, timeout: int = ..., files: list[Attachment] | None = None) -> ExecutionResult:
        """Execute code with client-side timeout.

        Note: This uses client-side timeout via asyncio.wait_for() for per-execution
        control. The session also has a server-side timeout (sessionTimeoutSeconds)
        that limits the total session lifetime.

        Args:
            code (str): Python code to execute.
            timeout (int): Client-side timeout in seconds. Defaults to ClientConfig.DEFAULT_EXECUTION_TIMEOUT.
            files (list[Attachment] | None): Optional files to upload before execution.

        Returns:
            ExecutionResult: Structured result with status, stdout, stderr, error, and duration.
        """
    async def download_file(self, file_path: str) -> bytes | None:
        """Download file from Bedrock sandbox.

        Args:
            file_path (str): Path to the file in the sandbox.

        Returns:
            bytes | None: File content as bytes, or None if download fails.

        Raises:
            RuntimeError: If sandbox is not started.
        """
    async def terminate(self) -> None:
        """Terminate the Bedrock sandbox session.

        Cleans up the session and releases resources.
        """
