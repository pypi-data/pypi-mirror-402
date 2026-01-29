def get_time_to_next_level(k, n):
    if k == 0:
        return 1

    p_up = (n - k) / n
    p_down = k / n

    # Рекурсивно вычисляем время текущего шага через предыдущий
    return (1 + p_down * get_time_to_next_level(k - 1, n)) / p_up


# Для 4-мерного куба:
n = 4
total_time = sum(get_time_to_next_level(k, n) for k in range(n))

print(f"Результат для n=4: {total_time:.6f}")