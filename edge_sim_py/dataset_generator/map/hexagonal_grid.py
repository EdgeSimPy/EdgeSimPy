"""Contains a function that creates a set of map coordinates forming an hexagonal grid."""


def hexagonal_grid(x_size: int, y_size: int) -> list:
    """Creates a hexagonal grid to represent the map based on [1].

    [1] Aral, Atakan, Vincenzo Demaio, and Ivona Brandic. "ARES: Reliable and Sustainable Edge
    Provisioning for Wireless Sensor Networks." IEEE Transactions on Sustainable Computing (2021).

    Args:
        x_size (int): Horizontal size of the hexagonal grid.
        y_size (int): Vertical size of the hexagonal grid.

    Returns:
        map_coordinates (list): List of created map coordinates.
    """
    map_coordinates = []

    x_range = list(range(0, x_size * 2))
    y_range = list(range(0, y_size))

    for i, y in enumerate(y_range):
        for x in x_range:
            if x % 2 == i % 2:
                map_coordinates.append((x, y))

    return map_coordinates
