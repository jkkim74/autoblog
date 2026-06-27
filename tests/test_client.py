import anthropic
import pytest

from autoblog.config import GeneratorConfig
from autoblog.generators.client import build_client, resolve_model_id


def test_resolve_model_id_anthropic():
    assert resolve_model_id(GeneratorConfig(model="claude-opus-4-8")) == "claude-opus-4-8"


def test_resolve_model_id_bedrock_prefixes():
    cfg = GeneratorConfig(model="claude-opus-4-8", provider="bedrock", aws_region="us-east-1")
    assert resolve_model_id(cfg) == "anthropic.claude-opus-4-8"


def test_resolve_model_id_bedrock_no_double_prefix():
    cfg = GeneratorConfig(
        model="anthropic.claude-opus-4-8", provider="bedrock", aws_region="us-east-1"
    )
    assert resolve_model_id(cfg) == "anthropic.claude-opus-4-8"


def test_build_client_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert isinstance(build_client(GeneratorConfig()), anthropic.Anthropic)


def test_build_client_unknown_provider():
    with pytest.raises(ValueError, match="Unknown generator provider"):
        build_client(GeneratorConfig(provider="nope"))


def test_build_client_bedrock():
    pytest.importorskip("boto3")
    from anthropic import AnthropicBedrockMantle

    client = build_client(GeneratorConfig(provider="bedrock", aws_region="us-east-1"))
    assert isinstance(client, AnthropicBedrockMantle)
