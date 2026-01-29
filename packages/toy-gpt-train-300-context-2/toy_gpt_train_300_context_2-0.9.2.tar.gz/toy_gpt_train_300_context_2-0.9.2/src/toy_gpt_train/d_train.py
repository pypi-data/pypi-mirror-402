"""d_train.py - Training loop module.

Trains the SimpleNextTokenModel on a small token corpus
using a context-2 window (two tokens of context).

Responsibilities:
- Create ((token_{t-1}, token_t) -> next_token) training pairs
- Run a basic gradient-descent training loop
- Track loss and accuracy per epoch
- Write a CSV log of training progress
- Write inspectable training artifacts (vocabulary, weights, embeddings, meta)

Concepts:
- context-2: predict the next token using (previous token, current token)
- epoch: one complete pass through all training pairs
- softmax: converts raw scores into probabilities (so predictions sum to 1)
- cross-entropy loss: measures how well predicted probabilities match the correct next token
- gradient descent: iterative weight updates to reduce prediction error
  - think descending to find the bottom of a valley in a landscape
  - where the valley floor corresponds to lower prediction error

Notes:
- This remains intentionally simple: no deep learning framework, no Transformer.
- The model generalizes n-gram training by expanding the context window.
- Training updates weight rows associated with the observed context-2 pattern.
- token_embeddings.csv remains a derived visualization artifact;
  learned embeddings are introduced in later stages.
"""

import logging
from pathlib import Path
from typing import Final

from datafun_toolkit.logger import get_logger, log_header

from toy_gpt_train.c_model import SimpleNextTokenModel
from toy_gpt_train.io_artifacts import (
    RowLabeler,
    VocabularyLike,
    find_single_corpus_file,
    write_artifacts,
    write_training_log,
)
from toy_gpt_train.math_training import argmax, cross_entropy_loss

LOG: logging.Logger = get_logger("TRAIN", level="INFO")

BASE_DIR: Final[Path] = Path(__file__).resolve().parents[2]
OUTPUTS_DIR: Final[Path] = BASE_DIR / "outputs"
TRAIN_LOG_PATH: Final[Path] = OUTPUTS_DIR / "train_log.csv"

type Context2 = tuple[int, int]
type Context2Pair = tuple[Context2, int]


def token_row_index_context2(context_ids: Context2, vocab_size: int) -> int:
    """Return the row index for a context-2 token sequence.

    Context order:
        (token_id_{t-1}, token_id_t)

    Flattening scheme:
        row_index = prev * vocab_size + curr

    This is the context-2 analogue of:
        unigram: row = token_id
    """
    token_id_t_minus_1, token_id_t = context_ids
    return token_id_t_minus_1 * vocab_size + token_id_t


def row_labeler_context2(vocab: VocabularyLike, vocab_size: int) -> RowLabeler:
    """Map a context-2 row index to a label like 'tok_{t-1}|tok_t'."""

    def label(row_idx: int) -> str:
        token_id_t_minus_1: int = row_idx // vocab_size
        token_id_t: int = row_idx % vocab_size

        tok1: str = vocab.get_id_token(token_id_t_minus_1) or f"id_{token_id_t_minus_1}"
        tok0: str = vocab.get_id_token(token_id_t) or f"id_{token_id_t}"

        return f"{tok1}|{tok0}"

    return label


def make_training_pairs(token_ids: list[int]) -> list[Context2Pair]:
    """Convert token IDs into ((t-1, t), next) training pairs.

    Example:
        ids = [3, 1, 2, 4]
        pairs = [((3, 1), 2), ((1, 2), 4)]
    """
    pairs: list[Context2Pair] = []
    for i in range(len(token_ids) - 2):
        context_ids: Context2 = (token_ids[i], token_ids[i + 1])
        next_id: int = token_ids[i + 2]
        pairs.append((context_ids, next_id))
    return pairs


def train_model(
    model: "SimpleNextTokenModel",
    pairs: list[Context2Pair],
    learning_rate: float,
    epochs: int,
) -> list[dict[str, float]]:
    """Train the model using gradient descent on softmax cross-entropy (context-2).

    Each example:
        context_ids = (token_id_{t-1}, token_id_t)
        target_id   = token_id_{t+1}

    Returns:
        A list of per-epoch metrics dictionaries (epoch, avg_loss, accuracy).
    """
    history: list[dict[str, float]] = []
    vocab_size: int = model.vocab_size

    for epoch in range(1, epochs + 1):
        total_loss: float = 0.0
        correct: int = 0

        for context_ids, target_id in pairs:
            previous_id, current_id = context_ids

            # Forward pass: probabilities for next token given (t-1, t).
            probs: list[float] = model.forward(previous_id, current_id)

            # Loss: cross-entropy for the correct next token.
            loss: float = cross_entropy_loss(probs, target_id)
            total_loss += loss

            # Accuracy: did the top prediction match the target?
            pred_id: int = argmax(probs)
            if pred_id == target_id:
                correct += 1

            # Backward pass for softmax cross-entropy:
            #   grad[j] = probs[j] - y[j]  where y is one-hot(target_id)
            #
            # Update the weight row for this specific (t-1, t) context.
            row_idx: int = token_row_index_context2(context_ids, vocab_size=vocab_size)
            row: list[float] = model.weights[row_idx]

            for j in range(vocab_size):
                y: float = 1.0 if j == target_id else 0.0
                grad: float = probs[j] - y
                row[j] -= learning_rate * grad

        avg_loss: float = total_loss / len(pairs) if pairs else float("nan")
        accuracy: float = correct / len(pairs) if pairs else 0.0

        history.append(
            {
                "epoch": float(epoch),
                "avg_loss": avg_loss,
                "accuracy": accuracy,
            }
        )

        LOG.info(
            f"Epoch {epoch}/{epochs} | avg_loss={avg_loss:.6f} | accuracy={accuracy:.3f}"
        )

    return history


def main() -> None:
    """Run a simple training demo end-to-end (context-2)."""
    from toy_gpt_train.a_tokenizer import CORPUS_DIR, SimpleTokenizer
    from toy_gpt_train.b_vocab import Vocabulary

    log_header(LOG, "Training Demo: Next-Token Softmax Regression (Context-2)")

    # Step 0: Identify the corpus file (single file rule).
    corpus_path: Path = find_single_corpus_file(CORPUS_DIR)

    # Step 1: Load and tokenize the corpus.
    tokenizer: SimpleTokenizer = SimpleTokenizer(corpus_path=corpus_path)
    tokens: list[str] = tokenizer.get_tokens()

    if len(tokens) < 3:
        LOG.error("Need at least 3 tokens for context-2 training (t-1, t -> next).")
        return

    # Step 2: Build vocabulary (maps tokens <-> integer IDs).
    vocab: Vocabulary = Vocabulary(tokens)
    vocab_size: int = vocab.vocab_size()

    # Step 3: Convert token strings to integer IDs for training.
    token_ids: list[int] = []
    for tok in tokens:
        tok_id: int | None = vocab.get_token_id(tok)
        if tok_id is None:
            LOG.error("Token not found in vocabulary: %r", tok)
            return
        token_ids.append(tok_id)

    # Step 4: Create training pairs (context-2 -> next).
    pairs: list[Context2Pair] = make_training_pairs(token_ids)
    LOG.info(f"Created {len(pairs)} training pairs.")

    # Step 5: Initialize model with zero weights (context-2 table lives in c_model.py).
    model: SimpleNextTokenModel = SimpleNextTokenModel(vocab_size=vocab_size)

    # Step 6: Train the model.
    learning_rate: float = 0.1
    epochs: int = 50

    history: list[dict[str, float]] = train_model(
        model=model,
        pairs=pairs,
        learning_rate=learning_rate,
        epochs=epochs,
    )

    # Step 7: Save training metrics for analysis.
    write_training_log(TRAIN_LOG_PATH, history)

    # Step 7b: Write inspectable artifacts for downstream use.
    write_artifacts(
        base_dir=BASE_DIR,
        corpus_path=corpus_path,
        vocab=vocab,
        model=model,
        model_kind="context2",
        learning_rate=learning_rate,
        epochs=epochs,
        row_labeler=row_labeler_context2(vocab, vocab_size),
    )

    # Step 8: Qualitative check - what does the model predict after the first 2 tokens?
    previous_token: str = tokens[0]
    current_token: str = tokens[1]

    previous_id: int | None = vocab.get_token_id(previous_token)
    current_id: int | None = vocab.get_token_id(current_token)

    if previous_id is None or current_id is None:
        LOG.error("One of the sample tokens was not found in vocabulary.")
        return

    probs: list[float] = model.forward(previous_id, current_id)
    best_next_id: int = argmax(probs)
    best_next_tok: str | None = vocab.get_id_token(best_next_id)

    LOG.info(
        f"After training, most likely next token after {previous_token!r}|{current_token!r} is {best_next_tok!r} (ID: {best_next_id})."
    )


if __name__ == "__main__":
    main()
