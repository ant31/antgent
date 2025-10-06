from collections.abc import Generator
from typing import Any, Self


class AliasResolver(dict[str, str]):
    """
    A class to resolve aliases, handling direct alias chains and detecting circular dependencies.
    This class inherits from dict and uses standard dictionary operations for
    adding, updating, and removing aliases, while enforcing string types for
    both aliases (keys) and their direct values.
    The resolve method follows a chain of aliases until a value is found that is
    not itself an alias key. If the initial alias is not found, it returns the input alias.
    It does not perform string substitution within values.
    """

    def __init__(self, initial_aliases: dict[str, str] | None = None):
        """
        Initializes the AliasResolver with an optional dictionary of aliases.

        Args:
            initial_aliases (dict, optional): A dictionary where keys are aliases
                                          and values are their corresponding values.
                                          Defaults to None, which means an empty alias set.
                                          Both keys and values in initial_aliases must be strings.
        """
        super().__init__()
        if initial_aliases:
            for alias, value in initial_aliases.items():
                self[alias] = value

    def add_aliases(self, aliases: dict[str, str] | Self) -> Self:
        """
        Adds a dictionary of aliases to the current AliasResolver instance.

        Args:
            aliases (dict): A dictionary where keys are aliases and values are their corresponding values.

        Returns:
            Self: The current instance of AliasResolver.
        """

        for alias, value in aliases.items():
            self[alias] = value
        return self

    def __setitem__(self, alias: str, value: str):
        """
        Sets an alias (key) to a given value, enforcing that both are strings.
        This overrides the default dict.__setitem__.

        Args:
            alias (str): The name of the alias (key).
            value (str): The value the alias should resolve to or point to.

        Raises:
            TypeError: If alias or value is not a string.
        """
        if not isinstance(alias, str):
            raise TypeError("Alias name (key) must be a string.")
        if not isinstance(value, str):
            raise TypeError("Alias value must be a string.")
        super().__setitem__(alias, value)

    def resolve(self, alias_name: str) -> str:
        """
        Resolves an alias to its final value by following direct alias chains.
        If alias A points to "B", and B points to "final_value", then resolve(A) yields "final_value".
        If the initial alias_name is not found in the dictionary, it returns alias_name itself.
        It does not perform substitution of aliases within string values
        (e.g., if A="val_B_end" and B="mid", resolve(A) is "val_B_end", not "val_mid_end").

        Args:
            alias_name (str): The alias to resolve.

        Returns:
            str: The final resolved value, or alias_name if it's not a defined alias.

        Raises:
            TypeError: If alias_name is not a string.
            ValueError: If a circular dependency is detected in the alias chain.
        """
        if not isinstance(alias_name, str):
            raise TypeError("Alias name to resolve must be a string.")

        # If the initial alias_name is not a defined alias, return it directly.
        if alias_name not in self:
            return alias_name

        # Path tracks the sequence of alias *names* encountered in the current resolution chain
        path = [alias_name]
        # current_target_value is the value that the most recently resolved alias_name points to
        current_target_value = self[alias_name]

        # Continue as long as the current_target_value is itself an alias name (a key in our dictionary)
        while current_target_value in self:
            # The current_target_value is an alias name, let's call it next_alias_in_chain
            next_alias_in_chain = current_target_value

            # Check for circular dependency before trying to resolve next_alias_in_chain
            if next_alias_in_chain in path:
                path.append(next_alias_in_chain)  # Add the looping element to show the full loop
                raise ValueError(f"Circular dependency detected: {' -> '.join(path)}")

            path.append(next_alias_in_chain)  # Add this intermediate alias name to the path
            current_target_value = self[next_alias_in_chain]  # Get the value of this next alias in the chain

        # The loop terminates when current_target_value is no longer a key in self,
        # meaning it's the final resolved value.
        return current_target_value

    @classmethod
    def __get_validators__(cls: type["AliasResolver"]) -> Generator:
        """
        Pydantic specific method to provide validation functions.
        """
        yield cls.validate

    @classmethod
    def validate(cls: type["AliasResolver"], value: Any, info: Any) -> "AliasResolver":
        """
        Pydantic validator function.
        Ensures the input can be turned into an AliasResolver.
        """
        _ = info
        if isinstance(value, cls):
            return value  # Already an AliasResolver instance
        if not isinstance(value, dict):
            raise ValueError(f"Input must be a dictionary to create AliasResolver, got {type(value).__name__}")

        # Attempt to create an AliasResolver instance.
        # The __init__ and __setitem__ methods will handle type enforcement.
        # If they raise TypeError, we convert it to ValueError for Pydantic.
        try:
            return cls(initial_aliases=value)
        except TypeError as e:  # Catch TypeErrors from __setitem__ during __init__
            raise ValueError(str(e)) from e  # Pydantic expects ValueError for validation failures


Aliases = AliasResolver()
