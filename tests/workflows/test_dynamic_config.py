import pytest

from antgent.aliases import AliasResolver
from antgent.models.agent import AgentConfig, DynamicAgentConfig, ModelInfo
from antgent.workflows.base import BaseWorkflow, WorkflowInput


class TestDynamicAgentConfig:
    """Tests for the DynamicAgentConfig model."""

    def test_empty_config(self):
        """Test that an empty DynamicAgentConfig can be created."""
        config = DynamicAgentConfig()
        assert config.model is None
        assert config.aliases == {}
        assert config.agents == {}

    def test_global_model_override(self):
        """Test setting a global model override."""
        config = DynamicAgentConfig(model="gpt-4o")
        assert config.model == "gpt-4o"
        assert config.aliases == {}
        assert config.agents == {}

    def test_aliases_only(self):
        """Test setting only aliases."""
        config = DynamicAgentConfig(
            aliases={
                "fast-model": "gpt-3.5-turbo",
                "smart-model": "gpt-4o",
            }
        )
        assert config.model is None
        assert config.aliases == {"fast-model": "gpt-3.5-turbo", "smart-model": "gpt-4o"}
        assert config.agents == {}

    def test_per_agent_config(self):
        """Test setting per-agent configuration."""
        config = DynamicAgentConfig(
            agents={
                "SummaryAgent": ModelInfo(model="gpt-4o", client="openai"),
                "ClassifierAgent": ModelInfo(model="claude-3-opus", client="litellm"),
            }
        )
        assert config.model is None
        assert config.aliases == {}
        assert len(config.agents) == 2
        assert config.agents["SummaryAgent"].model == "gpt-4o"
        assert config.agents["ClassifierAgent"].model == "claude-3-opus"

    def test_full_config(self):
        """Test a complete configuration with all fields."""
        config = DynamicAgentConfig(
            model="gpt-4o",
            aliases={"fast": "gpt-3.5-turbo"},
            agents={
                "SpecialAgent": ModelInfo(
                    model="claude-3-opus",
                    client="litellm",
                    api_mode="chat",
                    max_input_tokens=8000,
                )
            },
        )
        assert config.model == "gpt-4o"
        assert config.aliases == {"fast": "gpt-3.5-turbo"}
        assert config.agents["SpecialAgent"].model == "claude-3-opus"
        assert config.agents["SpecialAgent"].max_input_tokens == 8000


class TestBaseWorkflowDynamicConfig:
    """Tests for the _apply_dynamic_config method in BaseWorkflow."""

    @pytest.fixture
    def base_agents_config(self):
        """Fixture providing a base agent configuration."""
        return {
            "Agent1": AgentConfig(name="Agent1", model="default-model-1", client="openai", api_key="agent1-key"),
            "Agent2": AgentConfig(name="Agent2", model="default-model-2", client="litellm", api_key="agent2-key"),
            "Agent3": AgentConfig(name="Agent3", model="default-model-3", client="gemini", api_key="agent3-key"),
        }

    @pytest.fixture
    def workflow_with_config(self, base_agents_config):
        """Fixture providing a workflow instance with base configuration."""
        workflow = BaseWorkflow()
        workflow.agentsconf = base_agents_config
        return workflow

    def test_no_dynamic_config(self, workflow_with_config):
        """Test that without dynamic config, original config is unchanged."""
        original = dict(workflow_with_config.agentsconf)
        
        # Apply None config - should return original
        result = workflow_with_config._apply_dynamic_config(DynamicAgentConfig())
        
        assert result == original

    def test_global_model_override_all_agents(self, workflow_with_config):
        """Test that global model override applies to all agents."""
        dynamic_config = DynamicAgentConfig(model="new-global-model")
        
        result = workflow_with_config._apply_dynamic_config(dynamic_config)
        
        # All agents should have the new model
        assert result["Agent1"].model == "new-global-model"
        assert result["Agent2"].model == "new-global-model"
        assert result["Agent3"].model == "new-global-model"
        
        # Other properties should remain unchanged
        assert result["Agent1"].client == "openai"
        assert result["Agent2"].client == "litellm"

    def test_per_agent_override(self, workflow_with_config):
        """Test that per-agent overrides work correctly - only model field."""
        dynamic_config = DynamicAgentConfig(
            agents={
                "Agent1": ModelInfo(model="agent1-specific-model", client="litellm"),
            }
        )
        
        result = workflow_with_config._apply_dynamic_config(dynamic_config)
        
        # Agent1 should have only the model overridden
        assert result["Agent1"].model == "agent1-specific-model"
        # All other fields should remain unchanged from base config
        assert result["Agent1"].client == "openai"
        
        # Other agents should be unchanged
        assert result["Agent2"].model == "default-model-2"
        assert result["Agent3"].model == "default-model-3"

    def test_precedence_per_agent_over_global(self, workflow_with_config):
        """Test that per-agent config takes precedence over global."""
        dynamic_config = DynamicAgentConfig(
            model="global-override",
            agents={
                "Agent2": ModelInfo(model="agent2-specific"),
            },
        )
        
        result = workflow_with_config._apply_dynamic_config(dynamic_config)
        
        # Agent2 should have the per-agent model (not the global)
        assert result["Agent2"].model == "agent2-specific"
        
        # Other agents should have the global override
        assert result["Agent1"].model == "global-override"
        assert result["Agent3"].model == "global-override"

    def test_create_new_agent_config(self, workflow_with_config):
        """Test that per-agent config can create new agent configurations."""
        dynamic_config = DynamicAgentConfig(
            agents={
                "NewAgent": ModelInfo(model="new-agent-model", client="openai"),
            }
        )
        
        result = workflow_with_config._apply_dynamic_config(dynamic_config)
        
        # New agent should be added
        assert "NewAgent" in result
        assert result["NewAgent"].model == "new-agent-model"
        assert result["NewAgent"].name == "NewAgent"
        
        # Existing agents should remain
        assert "Agent1" in result
        assert "Agent2" in result

    def test_modelinfo_all_fields(self, workflow_with_config):
        """Test that only the model field is applied, other fields are ignored."""
        dynamic_config = DynamicAgentConfig(
            agents={
                "Agent1": ModelInfo(
                    model="custom-model",
                    client="gemini",
                    api_mode="response",
                    max_input_tokens=10000,
                    base_url="https://custom.api.com",
                    api_key="secret-key-123",
                ),
            }
        )
        
        result = workflow_with_config._apply_dynamic_config(dynamic_config)
        
        agent1 = result["Agent1"]
        # Only model should be overridden
        assert agent1.model == "custom-model"
        # All other fields should remain unchanged from base config
        assert agent1.client == "openai"
        assert agent1.api_mode == "chat"  # Default value
        assert agent1.max_input_tokens is None  # Default value
        assert agent1.base_url is None  # Default value
        assert agent1.api_key == "agent1-key"  # Unchanged from base config

    def test_aliases_merging(self, workflow_with_config, monkeypatch):
        """Test that dynamic aliases are correctly merged into a new, per-workflow resolver."""
        from antgent.aliases import Aliases

        # Set up a global alias
        monkeypatch.setitem(Aliases, "global-alias", "global-value")
        monkeypatch.setitem(Aliases, "powerful-model", "global-gpt-4")

        dynamic_config = DynamicAgentConfig(
            aliases={
                "fast-model": "gpt-3.5-turbo",
                "powerful-model": "gpt-4o",  # This should override the global one
            }
        )

        # Apply the dynamic config
        workflow_with_config._apply_dynamic_config(dynamic_config)

        # Get the workflow-specific resolver
        resolver = workflow_with_config.alias_resolver

        # Verify the resolver is a new instance
        assert resolver is not Aliases
        assert isinstance(resolver, AliasResolver)

        # Verify aliases are correctly merged and overridden
        assert resolver.resolve("global-alias") == "global-value"
        assert resolver.resolve("fast-model") == "gpt-3.5-turbo"
        assert resolver.resolve("powerful-model") == "gpt-4o"  # Overridden value

    def test_complex_scenario(self, workflow_with_config):
        """Test a complex scenario with multiple overrides - only model field."""
        dynamic_config = DynamicAgentConfig(
            model="global-gpt-4",
            aliases={"alias1": "model1"},
            agents={
                "Agent1": ModelInfo(model="agent1-custom", client="gemini"),
                "Agent3": ModelInfo(
                    model="agent3-custom",
                    max_input_tokens=5000,
                    api_key="custom-key",
                ),
                "NewAgent": ModelInfo(model="new-model"),
            },
        )
        
        result = workflow_with_config._apply_dynamic_config(dynamic_config)
        
        # Agent1: per-agent override (only model)
        assert result["Agent1"].model == "agent1-custom"
        assert result["Agent1"].client == "openai"  # unchanged from base
        
        # Agent2: global override only
        assert result["Agent2"].model == "global-gpt-4"
        assert result["Agent2"].client == "litellm"  # unchanged from base
        
        # Agent3: per-agent override (only model, other fields ignored)
        assert result["Agent3"].model == "agent3-custom"
        assert result["Agent3"].max_input_tokens is None  # unchanged from base (default)
        assert result["Agent3"].api_key == "agent3-key"  # unchanged from base config
        
        # NewAgent: created from scratch with only model set
        assert "NewAgent" in result
        assert result["NewAgent"].model == "new-model"


class TestWorkflowInputWithDynamicConfig:
    """Tests for WorkflowInput with agent_config."""

    def test_input_without_agent_config(self):
        """Test that WorkflowInput works without agent_config."""
        from pydantic import BaseModel

        from antgent.models.agent import AgentInput
        
        class TestContext(BaseModel):
            text: str
        
        agent_input = AgentInput(context=TestContext(text="test"))
        workflow_input = WorkflowInput(agent_input=agent_input)
        
        assert workflow_input.agent_config is None
        assert workflow_input.agent_input.context.text == "test"

    def test_input_with_agent_config(self):
        """Test that WorkflowInput works with agent_config."""
        from pydantic import BaseModel

        from antgent.models.agent import AgentInput
        
        class TestContext(BaseModel):
            text: str
        
        agent_input = AgentInput(context=TestContext(text="test"))
        dynamic_config = DynamicAgentConfig(model="gpt-4o")
        
        workflow_input = WorkflowInput(
            agent_input=agent_input,
            agent_config=dynamic_config,
        )
        
        assert workflow_input.agent_config is not None
        assert workflow_input.agent_config.model == "gpt-4o"

    def test_serialization_roundtrip(self):
        """Test that WorkflowInput can be serialized and deserialized."""
        from pydantic import BaseModel

        from antgent.models.agent import AgentInput
        
        class TestContext(BaseModel):
            text: str
        
        agent_input = AgentInput(context=TestContext(text="test"))
        dynamic_config = DynamicAgentConfig(
            model="gpt-4o",
            aliases={"fast": "gpt-3.5"},
            agents={
                "Agent1": ModelInfo(model="claude-3"),
            },
        )
        
        original = WorkflowInput(
            agent_input=agent_input,
            agent_config=dynamic_config,
        )
        
        # Serialize to dict and back
        data = original.model_dump()
        restored = WorkflowInput[TestContext].model_validate(data)
        
        assert restored.agent_config.model == "gpt-4o"
        assert restored.agent_config.aliases == {"fast": "gpt-3.5"}
        assert "Agent1" in restored.agent_config.agents
