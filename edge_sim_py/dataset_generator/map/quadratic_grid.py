"""Contains a function that creates a set of map coordinates forming a quadratic grid."""


def quadratic_grid(x_size: int, y_size: int) -> list:
    """Creates a quadratic grid to represent the map.

    Args:
        x_size (int): Horizontal size of the quadratic grid.
        y_size (int): Vertical size of the quadratic grid.

    Returns:
        map_coordinates (list): List of created map coordinates.
    """
    map_coordinates = []

    x_range = list(range(x_size))
    y_range = list(range(y_size))

    for i, y in enumerate(y_range):
        for x in x_range:
            map_coordinates.append((x, y))

    return map_coordinates
