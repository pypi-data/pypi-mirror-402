import torch as tc
import torch.nn as nn


class NESAdam:
    def __init__(
        s, net: nn.Module, lr=1e-2, pop_size=50, beta1=0.9, beta2=0.999, eps=1e-8
    ):
        s.net, s.lr, s.pop_size = net, lr, pop_size
        s.beta1, s.beta2, s.eps = beta1, beta2, eps
        s.params = list(s.net.parameters())
        s.x = nn.utils.parameters_to_vector(s.params)
        s.m = tc.zeros_like(s.x)  # 1st moment
        s.v = tc.zeros_like(s.x)  # 2nd moment
        s.t = 0

    def compute_ranks(s, x: tc.Tensor):
        ranks = tc.zeros(len(x))
        ranks[x.argsort()] = tc.linspace(-0.5, 0.5, len(x))
        return ranks

    @tc.no_grad()
    def step(s, loss_fn, std=0.02, weight_decay=0.01):
        s.t += 1
        half_pop = s.pop_size // 2
        u = tc.randn(half_pop, s.x.shape[0])
        losses = tc.zeros(s.pop_size)

        for i in range(half_pop):
            for j, sign in enumerate([1, -1]):
                nn.utils.vector_to_parameters(s.x + sign * u[i] * std, s.params)
                losses[i + j * half_pop] = loss_fn()

        # 1. Rank-based Fitness
        utilities = s.compute_ranks(-losses)
        w_pos, w_neg = utilities[:half_pop], utilities[half_pop:]

        # 2. Gradient Estimation
        g = tc.zeros_like(s.x)
        for i in range(half_pop):
            g += (w_pos[i] - w_neg[i]) * u[i]
        g /= s.pop_size * std

        # 3. Add Weight Decay (Standard SOTA practice)
        g -= weight_decay * s.x

        # 4. Adam Update (The "SOTA" engine)
        s.m = s.beta1 * s.m + (1 - s.beta1) * g
        s.v = s.beta2 * s.v + (1 - s.beta2) * (g**2)

        m_hat = s.m / (1 - s.beta1**s.t)
        v_hat = s.v / (1 - s.beta2**s.t)

        s.x += s.lr * m_hat / (tc.sqrt(v_hat) + s.eps)

        # 5. Push back to model
        nn.utils.vector_to_parameters(s.x, s.params)
        return losses.mean()
