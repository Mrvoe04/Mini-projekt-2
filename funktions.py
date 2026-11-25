from queue import PriorityQueue

def calculate_path_cost(world, path):
    total_cost = 0
    for index in range(1, len(path)):
        current = path[index - 1]
        next_position = path[index]
        total_cost += world.movement_cost(current, next_position)
    return total_cost

def find_path(world, start, goal):
    """
    
      Dijkstras algoritme.
    
    """
    frontier = PriorityQueue()
    frontier.put((0, start))

    came_from = {start: None}
    cost_so_far = {start: 0}

    while not frontier.empty():
        _, current = frontier.get()

        if current == goal:
            break

        for next_position in world.neighbors(current):
            new_cost = (
                cost_so_far[current]
                + world.movement_cost(current, next_position)
            )

            if (
                next_position not in cost_so_far
                or new_cost < cost_so_far[next_position]
            ):
                cost_so_far[next_position] = new_cost
                frontier.put((new_cost, next_position))
                came_from[next_position] = current

    if goal not in came_from:
        return []

    # Genskab ruten fra mål til start
    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = came_from[current]

    path.reverse()
    return path