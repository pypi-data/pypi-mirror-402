from typing import TypeVar, Callable

T = TypeVar('T')


def select_option(
    options: list[T],
    prompt: str,
    display_names: list[str] | None = None,
    to_display_name: Callable[[T], str] | None = None,
) -> T:
    """
    Interactive CLI option selector.

    Args:
        options: List of options to choose from
        prompt: Message to display to the user
        display_names: Optional list of display names for options
        to_display_name: Optional function to convert option to display name
            (used if display_names is not provided)

    Returns:
        The selected option

    Raises:
        ValueError: If options is empty or display_names length doesn't match
    """
    if not options:
        raise ValueError("Options list cannot be empty")

    if display_names is not None:
        if len(display_names) != len(options):
            raise ValueError("display_names must have same length as options")
        names = display_names
    elif to_display_name is not None:
        names = [to_display_name(opt) for opt in options]
    else:
        names = [str(opt) for opt in options]

    print(prompt)
    for i, name in enumerate(names, start=1):
        print(f"{i}. {name}")

    while True:
        try:
            choice = int(input())
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print("Please enter a valid number")
