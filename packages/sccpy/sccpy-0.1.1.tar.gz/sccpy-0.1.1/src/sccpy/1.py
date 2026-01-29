from functools import lru_cache
import sys

sys.setrecursionlimit(10**6)

@lru_cache(maxsize=None)
def expected_coins(n, p_index):
    # p_index от 0 до 10, где p = p_index / 10
    if n == 0:
        return 0.0

    p = p_index / 10.0

    # Орёл: выигрываем 1 тугрик, p уменьшается
    new_p_index_heads = max(0, p_index - 1)
    result_heads = 1.0 + expected_coins(n - 1, new_p_index_heads)

    # Решка: ничего не выигрываем, p увеличивается
    new_p_index_tails = min(10, p_index + 1)
    result_tails = expected_coins(n - 1, new_p_index_tails)

    return p * result_heads + (1 - p) * result_tails


# Начинаем с p = 0.5, это p_index = 5
result = expected_coins(2025, 5)
print(f"{result:.9f}")