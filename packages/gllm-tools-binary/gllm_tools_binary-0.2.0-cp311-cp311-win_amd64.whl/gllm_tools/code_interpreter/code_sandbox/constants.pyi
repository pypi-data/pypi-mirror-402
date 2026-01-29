from enum import StrEnum

class Language(StrEnum):
    """Programming languages supported by code sandbox."""
    PYTHON: str

class BedrockClientConfig:
    """Configuration for Bedrock client."""
    AWS_SERVICE_NAME: str
    CODE_INTERPRETER_ID: str
    DEFAULT_REGION: str
    DEFAULT_SESSION_TIMEOUT: int
    DEFAULT_EXECUTION_TIMEOUT: int
    SESSION_NAME_PREFIX: str

class BedrockAgentCoreSandboxOperation:
    """Operations supported by Bedrock AgentCore sandbox."""
    EXECUTE_CODE: str
    WRITE_FILES: str
    READ_FILES: str

class BedrockAgentCoreSandboxField:
    """Fields used by Bedrock AgentCore sandbox."""
    STREAM: str
    RESULT: str
    SESSION_ID: str
    IS_ERROR: str
    CONTENT: str
    TYPE: str
    TEXT: str
    DATA: str
    BLOB: str
    RESOURCE: str
    PATHS: str
    PATH: str
    LANGUAGE: str
    CODE: str
    STRUCTURED_CONTENT: str
    STDOUT: str
    STDERR: str

class BedrockAgentCoreSandboxContentType(StrEnum):
    """Content types used by Bedrock AgentCore sandbox."""
    TEXT: str
    IMAGE: str
    RESOURCE: str
    BLOB: str

class BedrockAgentCoreSandboxErrorMessage:
    """Error messages used by Bedrock AgentCore sandbox."""
    EXECUTION_FAILED: str
    UNSUPPORTED_LANGUAGE: str
    SESSION_START_FAILED: str
    SESSION_NOT_STARTED: str
    EXECUTION_TIMEOUT: str
