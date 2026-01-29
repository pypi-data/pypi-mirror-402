def solve():
    # p_j = 0.2 (минимум один такой элемент)
    # Сумма остальных p_i = 1 - 0.2 = 0.8
    # p_i >= 0.01
    # Чтобы максимизировать 1 - sum(p_i^2), нужно минимизировать sum(p_i^2)

    # Чтобы минимизировать сумму квадратов, нужно распределить 0.8
    # на как можно большее количество мелких частей.
    # Самая мелкая часть - 0.01.
    # Количество таких частей: 0.8 / 0.01 = 80.

    p_fixed = 0.2
    p_others = [0.01] * 80

    probabilities = [p_fixed] + p_others

    # Проверка условий
    assert abs(sum(probabilities) - 1.0) < 1e-9
    assert all(p >= 0.01 for p in probabilities)
    assert any(abs(p - 0.2) < 1e-9 for p in probabilities)

    sum_squares = sum(p ** 2 for p in probabilities)
    h_p = 1 - sum_squares

    return h_p


result = solve()
print(f"{result:.6f}")