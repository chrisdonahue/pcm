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


def sin_fast(cycle, size=4096):
    i_float = cycle * size
    i = int(i_float)
    alpha = i_float - i
    table = sin_table(size)
    return (1 - alpha) * table[i % size] + alpha * table[(i + 1) % size]


def fm(f_c, f_m, I, f_s, T):
    audio = [0.0] * int(f_s * T)  # audio buffer
    c_c, c_m = 0.0, 0.0  # carrier/modulator phase in cycles
    I /= 2.0 * math.pi  # index also in units of cycles
    d_c, d_m = f_c / f_s, f_m / f_s  # change in cycles per sample
    for i in range(len(audio)):
        audio[i] = sin_fast(c_c + I * sin_fast(c_m))
        c_c += d_c
        c_m += d_m
    return audio


if __name__ == "__main__":
    import time
    import soundfile as sf

    s = time.time()
    sound = fm(200.0, 20.0, 3, 44100, 2)
    e = time.time() - s

    sin_table()
    s = time.time()
    naive = fm_naive(200.0, 20.0, 3, 44100, 2)
    e_naive = time.time() - s

    assert len(sound) == len(naive)
    for i in range(len(sound)):
        assert abs(sound[i] - naive[i]) < 1e-5

    print(f"Wrote fm.wav, {e_naive / e}x speed relative to naive implementation")
    sf.write("fm.wav", sound, 44100)
