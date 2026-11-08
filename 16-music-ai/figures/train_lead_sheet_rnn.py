"""Train the lead sheet language model for notebooks/lead-sheets.ipynb.

This file is *not* student-facing. It trains a small recurrent neural network
(a plain "Elman" RNN) to predict the next token of a lead sheet (melody notes
and chords), on the TRAIN split of ../assets/TheorytabSimple.json.gz (written by
make_theorytab.py), and saves the weights with the best VALID loss, along with
the vocabulary, to ../assets/lead-sheet-rnn.npz (float32). Everything is numpy:
the forward pass, the cross-entropy loss, backpropagation through time, gradient
clipping, and Adam.

The tokenizer (VOCAB, events_to_tokens, tokens_to_events) and the RNN equations
are duplicated in the notebook, which only loads the trained weights and samples
from them. If you change one copy, change the other: the notebook checks that
its VOCAB matches the one saved here.

Tokens (115), with time shifts in the spirit of Performance RNN (Oore et al.
2018), plus bar lines:
    <BOS>, <EOS>                 the start and end of a song
    BAR                          the start of a new bar (4 beats, 16 sixteenths)
    CHORD_<root>:<family>  (60)  a new chord, e.g., CHORD_F#:min7
    NOTE_<pitch>           (37)  a melody note, MIDI pitch 48-84 (others are
                                 moved by octaves into this range)
    SHIFT_<k>              (15)  wait k = 1, ..., 15 sixteenth notes (within a bar)
Onsets are rounded to the nearest sixteenth note, and a chord comes before a
melody note with the same onset. Every bar starts with BAR, even an empty one.
We first tried time shifts alone (SHIFT_1 to SHIFT_16, which could cross bar
lines, and no BAR): the RNN then lost track of where the bar lines were, and
only about 20% of its sampled chord changes fell on the first beat of a bar
(versus 59% in the data). The BAR token fixes this (59% of sampled chord changes
fall on the first beat, at temperature 0.9) at the cost of one more token type
and about 1.5% longer sequences, since the RNN no longer has to count beats
across bars. It also lowers the loss for the same number of training steps.

The model reads one token x_t at a time and updates a hidden state:
    h_t = tanh(E[x_t] W_x + h_{t-1} W_h + b_h)
    P(x_{t+1} | x_1, ..., x_t) = softmax(h_t W_y + b_y)

Training uses random crops of 128 tokens from the concatenation of all TRAIN
songs, starting from h = 0, in batches of 64, with gradients clipped to a global
norm of 1 and an Adam learning rate that decays along a cosine from 1e-3. Each
crop is transposed by a random number of semitones (-6 to +5, notes and chord
roots alike), so the model sees every song in all 12 keys. Without this, the
model starts to overfit (VALID loss stalls while TRAIN loss keeps falling).
With it, TRAIN and VALID losses stay within about 0.01 nats of each other.
A learning rate of 3e-3 trained faster at first but was unstable (a 384-unit
RNN diverged).

We report the average negative log-likelihood (NLL) per token, in nats and
bits, on whole songs (each from <BOS> and h = 0, predicting every token after
<BOS>, including <EOS>), alongside unigram, bigram, and trigram baselines
(counts plus add-k smoothing, with k chosen on VALID).

Results of the default run (embedding 32, hidden 256, 107,219 parameters, a
0.44 MB file; 60,000 steps in about 18 minutes on an M-series laptop, plus about
2 minutes for the baselines), in nats (bits) per token:
                     VALID          TEST
    unigram          3.562 (5.139)  3.589 (5.178)
    bigram           2.783 (4.015)  2.801 (4.041)
    trigram          2.400 (3.462)  2.426 (3.499)
    RNN              1.615 (2.330)  1.640 (2.367)    (TRAIN: 1.617 (2.333))
A 512-unit RNN (361,779 parameters, 25,000 steps) reached only 1.619 on VALID.

Run with the project virtualenv:
    python train_lead_sheet_rnn.py
"""

import argparse
import gzip
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
DATASET = ASSETS / "TheorytabSimple.json.gz"
OUTPUT = ASSETS / "lead-sheet-rnn.npz"

# ---------------------------------------------------------------------------
# Tokenizer (duplicated in notebooks/lead-sheets.ipynb)
# ---------------------------------------------------------------------------

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FAMILIES = ["maj", "min", "7", "maj7", "min7"]
LOWEST, HIGHEST = 48, 84          # the range of melody pitches, C3 to C6
VOCAB = (["<BOS>", "<EOS>", "BAR"]
         + [f"CHORD_{root}:{family}" for root in PITCH_NAMES for family in FAMILIES]
         + [f"NOTE_{pitch}" for pitch in range(LOWEST, HIGHEST + 1)]
         + [f"SHIFT_{k}" for k in range(1, 16)])
INDEX = {token: i for i, token in enumerate(VOCAB)}


def events_to_tokens(melody: list, chords: list) -> list[int]:
    """A lead sheet as token indices: <BOS>, then each bar (of 4 beats) as a BAR token
    followed by its chords and notes in time order (a chord before a note at the same
    time), with SHIFT_k tokens that wait k sixteenth notes, then <EOS>. Onsets are
    rounded to sixteenths, and pitches are moved by octaves into range."""
    events = {}
    for beat, label in chords:
        events[round(4 * beat), 0] = f"CHORD_{label}"
    for beat, pitch in melody:
        while pitch < LOWEST:
            pitch += 12
        while pitch > HIGHEST:
            pitch -= 12
        events[round(4 * beat), 1] = f"NOTE_{pitch}"
    tokens, bar, position = ["<BOS>"], -1, 0
    for (sixteenth, _), token in sorted(events.items()):
        while bar < sixteenth // 16:              # start a new bar
            tokens.append("BAR")
            bar, position = bar + 1, 0
        if position < sixteenth % 16:             # wait until this event
            tokens.append(f"SHIFT_{sixteenth % 16 - position}")
            position = sixteenth % 16
        tokens.append(token)
    tokens.append("<EOS>")
    return [INDEX[token] for token in tokens]


def tokens_to_events(tokens: list[int]) -> tuple[list, list]:
    """The melody ([beat, pitch] pairs) and chords ([beat, label] pairs) of a token
    sequence, up to the first <EOS>."""
    melody, chords, bar, position = [], [], -1, 0
    for token in tokens:
        kind, _, value = VOCAB[token].partition("_")
        if kind == "<EOS>":
            break
        elif kind == "BAR":
            bar, position = bar + 1, 0
        elif kind == "SHIFT":
            position += int(value)
        elif kind == "CHORD":
            chords.append([4 * bar + position / 4, value])
        elif kind == "NOTE":
            melody.append([4 * bar + position / 4, int(value)])
    return melody, chords


# ---------------------------------------------------------------------------
# The RNN language model
# ---------------------------------------------------------------------------


def init_params(vocab_size: int, embed_dim: int, hidden_dim: int,
                rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Random initial weights: Gaussian, except for an orthogonal recurrence matrix."""
    W_h, _ = np.linalg.qr(rng.normal(size=(hidden_dim, hidden_dim)))
    params = {
        "E": rng.normal(0, 1, (vocab_size, embed_dim)),
        "W_x": rng.normal(0, 1 / np.sqrt(embed_dim), (embed_dim, hidden_dim)),
        "W_h": W_h,
        "b_h": np.zeros(hidden_dim),
        "W_y": rng.normal(0, 1 / np.sqrt(hidden_dim), (hidden_dim, vocab_size)),
        "b_y": np.zeros(vocab_size),
    }
    return {name: p.astype(np.float32) for name, p in params.items()}


def rnn_forward(params: dict[str, np.ndarray], inputs: np.ndarray,
                h0: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Run the RNN over a batch of token sequences, inputs[t, b] (time first). Returns
    the logits of the next token at every step, (T, B, V), and every hidden state,
    (T + 1, B, H), starting from h0 (by default, zeros)."""
    T, B = inputs.shape
    H = params["W_h"].shape[0]
    a = params["E"][inputs] @ params["W_x"] + params["b_h"]   # the inputs' part, all at once
    h = np.zeros((T + 1, B, H), dtype=a.dtype)
    if h0 is not None:
        h[0] = h0
    for t in range(T):
        h[t + 1] = np.tanh(a[t] + h[t] @ params["W_h"])
    return h[1:] @ params["W_y"] + params["b_y"], h


def log_softmax(logits: np.ndarray) -> np.ndarray:
    """Log-probabilities from logits, along the last axis (numerically stable)."""
    logits = logits - logits.max(axis=-1, keepdims=True)
    return logits - np.log(np.exp(logits).sum(axis=-1, keepdims=True))


def cross_entropy(logits: np.ndarray, targets: np.ndarray) -> tuple[float, np.ndarray]:
    """The average negative log-likelihood of the targets, and its gradient with respect
    to the logits (softmax minus one-hot, averaged)."""
    log_p = log_softmax(logits)
    nll = -np.take_along_axis(log_p, targets[..., None], axis=-1).mean()
    dlogits = np.exp(log_p)
    np.put_along_axis(dlogits, targets[..., None],
                      np.take_along_axis(dlogits, targets[..., None], axis=-1) - 1, axis=-1)
    return float(nll), dlogits / targets.size


def rnn_backward(params: dict[str, np.ndarray], inputs: np.ndarray, h: np.ndarray,
                 dlogits: np.ndarray) -> dict[str, np.ndarray]:
    """Backpropagation through time: the gradient of the loss with respect to every
    parameter, given the forward pass's hidden states and the gradient of the logits."""
    T, B = inputs.shape
    H, V = params["W_y"].shape
    dh = dlogits @ params["W_y"].T                   # dloss/dh[t + 1] through the output
    da = np.zeros_like(dh)                           # dloss/d(pre-tanh activation)
    for t in reversed(range(T)):
        da[t] = dh[t] * (1 - h[t + 1] ** 2)          # back through the tanh
        if t > 0:
            dh[t - 1] += da[t] @ params["W_h"].T     # back through the recurrence
    da_flat = da.reshape(-1, H)
    grads = {
        "W_y": h[1:].reshape(-1, H).T @ dlogits.reshape(-1, V),
        "b_y": dlogits.sum(axis=(0, 1)),
        "W_h": h[:-1].reshape(-1, H).T @ da_flat,
        "W_x": params["E"][inputs].reshape(T * B, -1).T @ da_flat,
        "b_h": da_flat.sum(axis=0),
        "E": np.zeros_like(params["E"]),
    }
    np.add.at(grads["E"], inputs.reshape(-1), da_flat @ params["W_x"].T)
    return grads


def clip_gradients(grads: dict[str, np.ndarray], max_norm: float) -> float:
    """Rescale the gradients (in place) so that their global norm is at most max_norm."""
    norm = float(np.sqrt(sum((g.astype(np.float64) ** 2).sum() for g in grads.values())))
    if norm > max_norm:
        for g in grads.values():
            g *= max_norm / norm
    return norm


def adam_update(params: dict[str, np.ndarray], grads: dict[str, np.ndarray], state: dict,
                lr: float, beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8) -> None:
    """One step of Adam (Kingma and Ba 2015), in place."""
    state["step"] = step = state.get("step", 0) + 1
    for name, param in params.items():
        m = state.setdefault(f"m_{name}", np.zeros_like(param))
        v = state.setdefault(f"v_{name}", np.zeros_like(param))
        m += (1 - beta1) * (grads[name] - m)
        v += (1 - beta2) * (grads[name] ** 2 - v)
        m_hat, v_hat = m / (1 - beta1 ** step), v / (1 - beta2 ** step)
        param -= (lr * m_hat / (np.sqrt(v_hat) + eps)).astype(np.float32)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def songs_nll(params: dict[str, np.ndarray], songs: list[list[int]], batch_size: int = 128) -> float:
    """The average NLL per token (nats) of whole songs, each from <BOS> and h = 0. Songs
    are batched by length and padded, and padded positions are left out of the average."""
    order = sorted(range(len(songs)), key=lambda i: len(songs[i]))
    total, count = 0.0, 0
    for start in range(0, len(order), batch_size):
        batch = [songs[i] for i in order[start:start + batch_size]]
        T = max(len(song) for song in batch) - 1
        tokens = np.full((T + 1, len(batch)), INDEX["<EOS>"])
        mask = np.zeros((T, len(batch)), dtype=bool)
        for b, song in enumerate(batch):
            tokens[:len(song), b] = song
            mask[:len(song) - 1, b] = True
        logits, _ = rnn_forward(params, tokens[:-1])
        log_p = np.take_along_axis(log_softmax(logits), tokens[1:, :, None], axis=-1)[..., 0]
        total -= float(log_p[mask].sum())
        count += int(mask.sum())
    return total / count


def ngram_nll(train: list[list[int]], test: list[list[int]], n: int, k: float) -> float:
    """The average NLL per token (nats) of an n-gram model with add-k smoothing, counted
    on the training songs. Contexts are padded with <BOS> at the start of each song."""
    V = len(VOCAB)
    pad = [INDEX["<BOS>"]] * (n - 2)
    counts, totals = {}, {}
    for song in train:
        song = pad + song
        for i in range(n - 1, len(song)):
            context = tuple(song[i - n + 1:i])
            counts[context + (song[i],)] = counts.get(context + (song[i],), 0) + 1
            totals[context] = totals.get(context, 0) + 1
    total, count = 0.0, 0
    for song in test:
        song = pad + song
        for i in range(max(n - 1, len(pad) + 1), len(song)):
            context = tuple(song[i - n + 1:i])
            p = (counts.get(context + (song[i],), 0) + k) / (totals.get(context, 0) + k * V)
            total -= np.log(p)
            count += 1
    return total / count


def transposition_table() -> np.ndarray:
    """table[s + 6, token] is the token transposed by s semitones (s = -6, ..., 5): notes
    move by s (folded back into range by octaves), chord roots move by s, and every
    other token stays the same. Used to augment the training data with all 12 keys."""
    table = np.zeros((12, len(VOCAB)), dtype=np.int64)
    for s in range(-6, 6):
        for i, token in enumerate(VOCAB):
            kind, _, value = token.partition("_")
            if kind == "NOTE":
                pitch = int(value) + s
                pitch += 12 * (pitch < LOWEST) - 12 * (pitch > HIGHEST)
                token = f"NOTE_{pitch}"
            elif kind == "CHORD":
                root, family = value.split(":")
                token = f"CHORD_{PITCH_NAMES[(PITCH_NAMES.index(root) + s) % 12]}:{family}"
            table[s + 6, i] = INDEX[token]
    return table


def report(name: str, nll: float, songs: list[list[int]]) -> None:
    """Print an average NLL per token, in nats and bits, and the total per song (which,
    unlike the per-token average, is comparable across tokenizations)."""
    per_song = nll * sum(len(song) - 1 for song in songs) / len(songs)
    print(f"  {name:<28} {nll:.3f} nats/token  ({nll / np.log(2):.3f} bits/token, "
          f"{per_song:.1f} nats/song)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed_dim", type=int, default=32)
    parser.add_argument("--hidden_dim", type=int, default=256)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--seq_len", type=int, default=128)
    parser.add_argument("--steps", type=int, default=60000)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--min_lr", type=float, default=5e-5)
    parser.add_argument("--max_norm", type=float, default=1.0)
    parser.add_argument("--eval_every", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--skip_baselines", action="store_true")
    parser.add_argument("--no_transpose", action="store_true",
                        help="don't transpose each training crop by a random number of semitones")
    args = parser.parse_args()
    print(vars(args))

    with gzip.open(DATASET, "rt") as f:
        dataset = json.load(f)
    songs = {"TRAIN": [], "VALID": [], "TEST": []}
    for example in dataset.values():
        songs[example["split"]].append(events_to_tokens(example["melody"], example["chords"]))
    for split, split_songs in songs.items():
        print(f"{split}: {len(split_songs)} songs, {sum(map(len, split_songs))} tokens")

    # Round-trip test: tokens -> events -> tokens is the identity.
    for song in songs["VALID"]:
        assert events_to_tokens(*tokens_to_events(song)) == song

    if not args.skip_baselines:
        print("Baselines (VALID):")
        for n in [1, 2, 3]:
            best_k = min([0.001, 0.01, 0.1, 1.0],
                         key=lambda k: ngram_nll(songs["TRAIN"], songs["VALID"], n, k))
            report(f"{n}-gram (add-{best_k})", ngram_nll(songs["TRAIN"], songs["VALID"], n, best_k),
                   songs["VALID"])
            report("  ... on TEST", ngram_nll(songs["TRAIN"], songs["TEST"], n, best_k), songs["TEST"])

    rng = np.random.default_rng(args.seed)
    params = init_params(len(VOCAB), args.embed_dim, args.hidden_dim, rng)
    print(f"{sum(p.size for p in params.values())} parameters:",
          {name: p.shape for name, p in params.items()})
    stream = np.concatenate([np.array(song) for song in songs["TRAIN"]])
    transpose = transposition_table()
    train_subset = [songs["TRAIN"][i] for i in rng.choice(len(songs["TRAIN"]), 1000, replace=False)]

    state, best_valid, losses = {}, np.inf, []
    start_time = time.time()
    for step in range(1, args.steps + 1):
        starts = rng.integers(0, len(stream) - args.seq_len - 1, size=args.batch_size)
        crops = stream[starts + np.arange(args.seq_len + 1)[:, None]]    # (T + 1, B)
        if not args.no_transpose:
            crops = transpose[rng.integers(0, 12, size=args.batch_size), crops]
        logits, h = rnn_forward(params, crops[:-1])
        loss, dlogits = cross_entropy(logits, crops[1:])
        grads = rnn_backward(params, crops[:-1], h, dlogits)
        clip_gradients(grads, args.max_norm)
        progress = (step - 1) / args.steps
        lr = args.min_lr + 0.5 * (args.lr - args.min_lr) * (1 + np.cos(np.pi * progress))
        adam_update(params, grads, state, lr)
        losses.append(loss)

        if step % args.eval_every == 0 or step == args.steps:
            valid = songs_nll(params, songs["VALID"])
            train = songs_nll(params, train_subset)
            marker = ""
            if valid < best_valid:
                best_valid = valid
                np.savez(args.output, vocab=np.array(VOCAB),
                         valid_bits_per_token=np.float32(valid / np.log(2)), **params)
                marker = " (saved)"
            print(f"step {step:6d}  {time.time() - start_time:7.1f} s  lr {lr:.5f}  "
                  f"crop loss {np.mean(losses):.3f}  train {train:.3f}  valid {valid:.3f}{marker}",
                  flush=True)
            losses = []

    # Final report on the best weights.
    weights = np.load(args.output)
    params = {name: weights[name] for name in params}
    assert list(weights["vocab"]) == VOCAB
    print(f"Best weights ({args.output.stat().st_size / 1e6:.2f} MB):")
    report("RNN TRAIN (1000 songs)", songs_nll(params, train_subset), train_subset)
    report("RNN VALID", songs_nll(params, songs["VALID"]), songs["VALID"])
    report("RNN TEST", songs_nll(params, songs["TEST"]), songs["TEST"])


if __name__ == "__main__":
    main()
