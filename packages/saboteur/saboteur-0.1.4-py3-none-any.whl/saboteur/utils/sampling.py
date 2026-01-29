import random


def uniform_sample_from_dict(data: dict, stop_threshold=0.5) -> tuple[list[str], object]:
    key_paths: list[str] = []

    def _sample(d: dict) -> tuple[str, object]:
        probability = random.uniform(0, 1)
        key_list = list(d.keys())
        random_key = random.choice(key_list)
        key_paths.append(random_key)
        random_value = d[random_key]
        if probability < stop_threshold or not isinstance(random_value, dict):
            return random_value
        else:
            return _sample(d[random_key])

    random_value = _sample(data)
    return key_paths, random_value
