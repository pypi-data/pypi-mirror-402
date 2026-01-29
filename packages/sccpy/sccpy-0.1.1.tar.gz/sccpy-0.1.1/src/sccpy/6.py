from functools import lru_cache


@lru_cache(None)
def get_max_win_prob(tim_glads, max_glads):
    # Если у Максима кончились бойцы - он проиграл (вероятность 0)
    if not max_glads: return 0.0
    # Если у Тимофея кончились - Максим выиграл (вероятность 1)
    if not tim_glads: return 1.0

    # Тимофей выбирает своего бойца i, чтобы МИНИМИЗИРОВАТЬ победу Максима
    best_prob_for_tim = 1.0

    for i in range(len(tim_glads)):
        # Максим выбирает своего бойца j, чтобы МАКСИМИЗИРОВАТЬ свою победу
        best_prob_for_max = 0.0

        for j in range(len(max_glads)):
            t = tim_glads[i]
            m = max_glads[j]

            # Вероятности исхода одного боя
            p_tim_wins = t / (t + m)
            p_max_wins = m / (t + m)

            # Состояния после боя
            # Вариант А: Победил Тимофей
            new_tim_a = tuple(sorted(tim_glads[:i] + tim_glads[i + 1:] + (t + m,)))
            new_max_a = tuple(sorted(max_glads[:j] + max_glads[j + 1:]))
            prob_a = get_max_win_prob(new_tim_a, new_max_a)

            # Вариант Б: Победил Максим
            new_tim_b = tuple(sorted(tim_glads[:i] + tim_glads[i + 1:]))
            new_max_b = tuple(sorted(max_glads[:j] + max_glads[j + 1:] + (t + m,)))
            prob_b = get_max_win_prob(new_tim_b, new_max_b)

            # Средняя вероятность при выборе конкретной пары (i, j)
            current_pair_prob = p_tim_wins * prob_a + p_max_wins * prob_b
            best_prob_for_max = max(best_prob_for_max, current_pair_prob)

        best_prob_for_tim = min(best_prob_for_tim, best_prob_for_max)

    return best_prob_for_tim


# Начальные силы
tim_start = (1, 4, 9, 16, 25)
max_start = (1, 2, 3, 4, 20)

final_result = get_max_win_prob(tim_start, max_start)
print(f"Точная вероятность: {final_result:.6f}")