import functools
import math


def sin_naive(x):
    # Maclaurin series: x - x^3/3! + x^5/5! - ...
    x = x - 2.0 * math.pi * math.floor((x + math.pi) / (2.0 * math.pi))
    result = 0.0
    term = x
    x2 = x * x
    for n in range(10):
        result += term
        term *= -x2 / ((2 * n + 2) * (2 * n + 3))
    return result


def fm_naive(f_c, f_m, I, f_s, T):
    audio = [0.0] * int(f_s * T)  # audio buffer
    for i in range(len(audio)):
        modulator = sin_naive(2.0 * math.pi * f_m * i / f_s)
        audio[i] = sin_naive(2.0 * math.pi * f_c * i / f_s + I * modulator)
    return audio


@functools.cache
def sin_table(size=4096):
    return [sin_naive(2.0 * math.pi * (i / size)) for i in range(size)]


def sin_fast(radians, size=4096):
    i_float = (radians % (2.0 * math.pi)) / (2.0 * math.pi) * size
    i = int(i_float)
    alpha = i_float - i
    table = sin_table(size)
    return (1 - alpha) * table[i % size] + alpha * table[(i + 1) % size]


def fm(f_c, f_m, I, f_s, T):
    audio = [0.0] * int(f_s * T)  # audio buffer
    p_c, p_m = 0.0, 0.0  # carrier/modulator phase in radians
    d_c, d_m = (2.0 * math.pi * f / f_s for f in (f_c, f_m))  # radians per sample
    for i in range(len(audio)):
        audio[i] = sin_fast(p_c + I * sin_fast(p_m))
        p_c, p_m = p_c + d_c, p_m + d_m
    return audio


if __name__ == "__main__":
    import time
    import soundfile as sf

    s = time.time()
    sound = fm(1092, 350, 1, 44100, 2)
    e = time.time() - s

    sin_table()
    s = time.time()
    naive = fm_naive(1092, 350, 1, 44100, 2)
    e_naive = time.time() - s

    assert len(sound) == len(naive)
    for i in range(len(sound)):
        assert abs(sound[i] - naive[i]) < 1e-5

    print(f"Wrote fm.wav, {e_naive / e}x speed relative to naive implementation")
    sf.write("fm.wav", sound, 44100)
