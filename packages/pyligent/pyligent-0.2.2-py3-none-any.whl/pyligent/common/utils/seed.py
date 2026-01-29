import random

import numpy as np
import torch


def set_seed(seed: int = 420):
    np.random.seed(seed)
    random.seed(seed)
    torch.random.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
