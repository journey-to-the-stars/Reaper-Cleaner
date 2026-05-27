import math


def knn(point, entities, k=3):
    candidates = []
    for entity in entities:
        if hasattr(entity, 'alive') and not entity.alive:
            continue
        ep = entity.rect.center if hasattr(entity, 'rect') else entity
        d = math.hypot(point.x - ep[0], point.y - ep[1])
        candidates.append((d, entity))

    candidates.sort(key=lambda pair: pair[0])
    return [entity for _, entity in candidates[:k]]


def knn_weighted(origin, heading, entities, k=3):
    candidates = []
    for entity in entities:
        if hasattr(entity, 'alive') and not entity.alive:
            continue
        ep = entity.rect.center if hasattr(entity, 'rect') else entity
        to_target = (ep[0] - origin.x, ep[1] - origin.y)
        dist = math.hypot(*to_target)
        if dist == 0:
            candidates.append((0.0, entity))
            continue
        dot = (heading[0] * to_target[0] + heading[1] * to_target[1]) / dist
        angle_penalty = 1.0 + 0.5 * (1.0 - max(-1.0, min(1.0, dot)))
        candidates.append((dist * angle_penalty, entity))

    candidates.sort(key=lambda pair: pair[0])
    return [entity for _, entity in candidates[:k]]
