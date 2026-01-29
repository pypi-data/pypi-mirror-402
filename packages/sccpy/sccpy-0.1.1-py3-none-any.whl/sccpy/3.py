import pandas as pd


def solve():
    df = pd.read_csv('input_file_0.csv')

    count = 0
    for index, row in df.iterrows():
        A = int(row['A'])
        B = int(row['B'])
        C = int(row['C'])
        D = int(row['D'])

        # Check K (Consistency Index)
        # K = (A+B)/B + (C+D)/D - ((A-B)*D + (C-D)*B)/(B*D)
        # Common denominator: B*D
        # Term 1 numerator: (A+B)*D
        # Term 2 numerator: (C+D)*B
        # Term 3 numerator: (A-B)*D + (C-D)*B

        k_num = (A + B) * D + (C + D) * B - ((A - B) * D + (C - D) * B)
        k_den = B * D

        k_is_int = (k_num % k_den == 0)

        # Check E (Inverse Consistency Index)
        # E = (A+B)/C + (B+C)/A + (C+A)/B
        # Common denominator: A*B*C
        # Term 1 num: (A+B)*A*B
        # Term 2 num: (B+C)*B*C
        # Term 3 num: (C+A)*A*C

        e_num = (A + B) * A * B + (B + C) * B * C + (C + A) * A * C
        e_den = A * B * C

        e_is_int = (e_num % e_den == 0)

        if k_is_int and e_is_int:
            count += 1

    print(count)


solve()