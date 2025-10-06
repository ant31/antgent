import pytest

from antgent.aliases import AliasResolver

# --- Pytest Tests (Adjusted for the updated resolve logic) ---

@pytest.fixture
def base_resolver():
    """
    Provides a resolver with some initial aliases.
    """
    return AliasResolver({
        "home": "/user/local",
        "docs": "home/documents",
        "pics": "home/pictures",
        "work_docs": "docs/work",
        "chain1": "chain2_key",
        "chain2_key": "chain3_key",
        "chain3_key": "final_link_value"
    })

@pytest.fixture
def empty_resolver():
    """Provides an empty resolver."""
    return AliasResolver()

# --- Test Cases for Initialization ---

def test_initialization_empty():
    resolver = AliasResolver()
    assert len(resolver) == 0

def test_initialization_with_valid_aliases():
    aliases = {"a": "b", "b": "c"}
    resolver = AliasResolver(aliases)
    assert resolver["a"] == "b"
    assert resolver["b"] == "c"
    assert len(resolver) == 2

@pytest.mark.parametrize("invalid_aliases", [
    ({123: "value"}),
    ({"key": 123})
])
def test_initialization_with_invalid_aliases(invalid_aliases):
    with pytest.raises(TypeError):
        AliasResolver(initial_aliases=invalid_aliases)

# --- Test Cases for __setitem__ ---

def test_setitem_valid(empty_resolver):
    resolver = empty_resolver
    resolver["new_alias"] = "new_value"
    assert resolver["new_alias"] == "new_value"
    resolver["new_alias"] = "updated_value"
    assert resolver["new_alias"] == "updated_value"

@pytest.mark.parametrize("key, value", [
    (123, "value"),
    ("key", 123),
])
def test_setitem_invalid_types(empty_resolver, key, value):
    resolver = empty_resolver
    with pytest.raises(TypeError):
        resolver[key] = value

# --- Test Cases for resolve method (updated logic) ---

@pytest.mark.parametrize("alias_to_resolve, expected_value", [
    ("home", "/user/local"),
    ("docs", "home/documents"),
    ("pics", "home/pictures"),
    ("work_docs", "docs/work"),
])
def test_resolve_direct_values(base_resolver, alias_to_resolve, expected_value):
    assert base_resolver.resolve(alias_to_resolve) == expected_value

def test_resolve_chained_successful(base_resolver, empty_resolver):
    assert base_resolver.resolve("chain1") == "final_link_value"

    resolver = empty_resolver
    resolver["level1"] = "level2_as_key"
    resolver["level2_as_key"] = "level3_as_key"
    resolver["level3_as_key"] = "final_chained_value"
    assert resolver.resolve("level1") == "final_chained_value"

def test_resolve_value_is_not_an_alias(empty_resolver):
    resolver = empty_resolver
    resolver["direct"] = "this_is_the_final_value"
    assert resolver.resolve("direct") == "this_is_the_final_value"

def test_resolve_non_existent_alias_returns_input(base_resolver):
    """Test resolving an alias that does not exist returns the input alias name."""
    assert base_resolver.resolve("non_existent_alias") == "non_existent_alias"
    # Test with an empty resolver as well
    empty_res = AliasResolver()
    assert empty_res.resolve("another_one") == "another_one"

def test_resolve_alias_name_not_string(base_resolver):
    with pytest.raises(TypeError, match=r"Alias name to resolve must be a string\."):
        base_resolver.resolve(123)  # type: ignore

# --- Test Cases for Loop Detection in resolve ---

@pytest.mark.parametrize("loop_setup, problematic_alias, expected_loop_path_str", [
    ({"a": "a"}, "a", "a -> a"),
    ({"a": "b", "b": "a"}, "a", "a -> b -> a"),
    ({"a": "b", "b": "c", "c": "a"}, "a", "a -> b -> c -> a"),
    ({"x": "y_key", "y_key": "z_key", "z_key": "x"}, "x", "x -> y_key -> z_key -> x"),
    (
        {"start_node": "node1", "node1": "node2", "node2": "node3", "node3": "node1"},
        "start_node",
        "start_node -> node1 -> node2 -> node3 -> node1",
    ),
])
def test_resolve_circular_dependency(empty_resolver, loop_setup, problematic_alias, expected_loop_path_str):
    resolver = empty_resolver
    for k, v in loop_setup.items():
        resolver[k] = v
    with pytest.raises(ValueError, match=f"Circular dependency detected: {expected_loop_path_str}"):
        resolver.resolve(problematic_alias)

# --- Test Cases for Deletion (__delitem__) ---

def test_delete_alias(base_resolver):
    resolver = base_resolver
    assert "docs" in resolver
    del resolver["docs"]
    assert "docs" not in resolver
    # After deletion, resolving "docs" should return "docs" itself.
    assert resolver.resolve("docs") == "docs"

def test_delete_non_existent_alias(base_resolver):
    with pytest.raises(KeyError): # Standard dict behavior for del
        del base_resolver["non_existent_alias_for_del"]

# --- Test Cases for Standard Dictionary Behavior ---
def test_len_method(empty_resolver):
    resolver = empty_resolver
    assert len(resolver) == 0
    resolver["a"] = "1"
    assert len(resolver) == 1

def test_in_operator(base_resolver):
    assert "home" in base_resolver
    assert "non_existent_key" not in base_resolver

def test_get_method(base_resolver):
    assert base_resolver.get("home") == "/user/local"
    assert base_resolver.get("docs") == "home/documents"
    assert base_resolver.get("chain1") == "chain2_key"
    assert base_resolver.get("non_existent_key") is None
    assert base_resolver.get("non_existent_key", "default_val") == "default_val"

def test_iteration(base_resolver):
    keys = []
    expected_keys = ["home", "docs", "pics", "work_docs", "chain1", "chain2_key", "chain3_key"]
    for key in base_resolver:
        keys.append(key)
    assert sorted(keys) == sorted(expected_keys)
