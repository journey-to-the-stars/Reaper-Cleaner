import math

def get_dist(pair):
    return pair[0]


def knn(point, entities, k=3):
    alive = [e for e in entities if not (hasattr(e, 'alive') and not e.alive)]
    with_dist = []
    for e in alive:
        ex, ey = e.rect.center if hasattr(e, 'rect') else e
        dx = point.x - ex
        dy = point.y - ey
        dist = math.sqrt(dx * dx + dy * dy)
        with_dist.append((dist, e))
    with_dist.sort(key=get_dist)
    return [e for _, e in with_dist[:k]]



