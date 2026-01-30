"""Utility functions for the `matching` submodule."""


def remap(x: float, o_min: float, o_max: float, n_min: float, n_max: float) -> float:
    """Linearly map one range to another. For example, if the original range is 0 to 10 and the new range is 0 to 5,
    and `x` value of 5 will result in an output of 2.5.

    This function can handle negative values and inverted ranges. If the input is -10 to 0 and the new range is 5 to
    10, the output will still be valid.

    Args:
        x (float): The value inside the old range to be remapped.
        o_min (float): Minimum value of the old range.
        o_max (float): Maximum value of the old range.
        n_min (float): Minimum value of the new range.
        n_max (float): Maximum value of the new range.

    Returns:
        result (float): `x` modified to be fit inside the new range.
    """
    # check reversed input range
    reverse_input = False
    old_min = min(o_min, o_max)
    old_max = max(o_min, o_max)
    if not old_min == o_min:
        reverse_input = True

    # check reversed output range
    reverse_output = False
    new_min = min(n_min, n_max)
    new_max = max(n_min, n_max)
    if not new_min == n_min:
        reverse_output = True

    portion = (x - old_min) * (new_max - new_min) / (old_max - old_min)
    if reverse_input:
        portion = (old_max - x) * (new_max - new_min) / (old_max - old_min)

    result = portion + new_min
    if reverse_output:
        result = new_max - portion

    return result


def ease(x: float, falloff: float = 4.8) -> float:
    """Returns $y$ according to the equation $y=1-(f*x^2)$, where $f$ is an arbitrary "falloff" value.

    Args:
        x (float): The value to be placed in the curve.
        falloff (float): An arbitrary value that determines how sharply the value for $y$ decreases as $x$ increases.
            Default is 4.8, picked simply because it gave fairly good results.

    Returns:
        y (float): The value placed in the curve.
    """
    return 1 - (falloff * x * x)
