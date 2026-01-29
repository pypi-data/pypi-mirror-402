import itertools
import math
import random

import numpy as np

from pyligent.core.action import DoneAction, NodeAction
from pyligent.core.path import GoldPath, Node
from pyligent.tasks.prime.state import PrimeState, PrimeStateEngine


def generate_n_plus_one_primes(n: int) -> list[int]:
    assert n > 1

    primes = []
    num = 2
    while len(primes) < n + 1:
        is_prime = True

        limit = math.isqrt(num)
        for p in primes:
            if p > limit:
                break
            if num % p == 0:
                is_prime = False
                break

        if is_prime:
            primes.append(num)
        num += 1

    return primes


class PrimeAdapter:
    def __init__(
        self,
        n_primes: int,
        max_prime_factor: int,
        train_size: int,
        test_size: int,
    ) -> None:
        self.n_primes = n_primes
        self.max_prime_factor = max_prime_factor
        self.max_gold_chain_len = self.n_primes * self.max_prime_factor

        n_plus_one_primes = generate_n_plus_one_primes(self.n_primes)

        self.primes = np.array(n_plus_one_primes[:-1])
        self.prime_to_idx = {int(p): i for i, p in enumerate(self.primes)}
        self.max_input = int(
            np.prod(
                [self.primes[i] ** self.max_prime_factor for i in range(self.n_primes)]
            )
        )
        self.total_variants = self.n_primes ** (self.max_prime_factor + 1) - 1

        self.train_size = train_size
        self.test_size = test_size

    def _generate_data(
        self,
        size: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        x = np.zeros(size, dtype=int)
        chain = np.zeros((size, self.max_gold_chain_len), dtype=int)
        chain_length = np.zeros(size, dtype=int)
        y = np.zeros(size, dtype=int)

        # Create an iterator over all exponent vectors
        exponent_combinations = itertools.product(
            range(self.max_prime_factor + 1), repeat=self.n_primes
        )

        # Sample 'size' unique items without creating a full list
        sampled_vectors = random.sample(
            list(itertools.islice(exponent_combinations, 10**6)), size
        )

        for idx, vector in enumerate(sampled_vectors):
            number = 1
            local_chain_len = 0
            for i, exponent in enumerate(vector):
                if exponent > 0:
                    number *= self.primes[i] ** exponent
                    for _ in range(exponent):
                        chain[idx][local_chain_len] = i
                        local_chain_len += 1
            y[idx] = chain[idx][local_chain_len - 1]
            chain_length[idx] = local_chain_len
            x[idx] = number

        return x, chain, chain_length, y

    def generate_golden_paths(self, size: int) -> list[GoldPath]:
        gold_dataset = []
        state_engine = PrimeStateEngine()
        xs, chains, chain_lens, __ = self._generate_data(size)
        for idx, x in enumerate(xs):
            chain = chains[idx]
            chain_len = chain_lens[idx]
            nodes = []
            root_node = Node(
                None, NodeAction(0, str(int(x))), state=PrimeState(initial_number=int(x))
            )
            nodes.append(root_node)
            for i, v in enumerate(chain[: chain_len - 1]):
                parent = nodes[-1]
                action = NodeAction(i + 1, str(self.primes[int(v.item())]))
                node = Node(
                    parent, action, state=state_engine.reduce(parent.state, action)
                )
                nodes.append(node)

            done_action = DoneAction(str(self.primes[int(chain[chain_len - 1].item())]))
            parent = nodes[-1]
            done_node = Node(
                nodes[-1],
                done_action,
                state=state_engine.reduce(parent.state, done_action),
            )
            nodes.append(done_node)

            gold_dataset.append(GoldPath(nodes))

        return gold_dataset
