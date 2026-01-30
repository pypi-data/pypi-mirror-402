import torch
from torch.optim import Optimizer
import math


class CircularExploreOptimizer(Optimizer):
    """
    Gradient-based optimizer with conditional circular exploration.
    """

    def __init__(
        self,
        params,
        lr=1e-3,
        eps=1e-6,
        explore_radius=1e-2,
        explore_expand=2.0,
        num_directions=8,
        max_radius_steps=3,
    ):
        defaults = dict(
            lr=lr,
            eps=eps,
            explore_radius=explore_radius,
            explore_expand=explore_expand,
            num_directions=num_directions,
            max_radius_steps=max_radius_steps,
        )
        super().__init__(params, defaults)

    @staticmethod
    def _random_unit_tensor(tensor):
        noise = torch.randn_like(tensor)
        return noise / (torch.norm(noise) + 1e-12)

    @torch.no_grad()
    def step(self, closure):
        loss = closure()
        loss_val = loss.item()

        for group in self.param_groups:
            lr = group["lr"]
            eps = group["eps"]
            r0 = group["explore_radius"]
            expand = group["explore_expand"]
            K = group["num_directions"]
            max_steps = group["max_radius_steps"]

            grad_norm = 0.0
            for p in group["params"]:
                if p.grad is not None:
                    grad_norm += p.grad.norm().item() ** 2
            grad_norm = math.sqrt(grad_norm)

            # Gradient mode
            if grad_norm > eps:
                for p in group["params"]:
                    if p.grad is not None:
                        p.add_(p.grad, alpha=-lr)
                continue

            # Exploration mode
            best_loss = loss_val
            best_params = None
            original_params = [p.clone() for p in group["params"]]

            r = r0
            for _ in range(max_steps):
                for _ in range(K):
                    directions = [
                        self._random_unit_tensor(p) for p in group["params"]
                    ]
                    for p, d in zip(group["params"], directions):
                        p.add_(d, alpha=r)

                    new_loss = closure().item()

                    if new_loss < best_loss:
                        best_loss = new_loss
                        best_params = [p.clone() for p in group["params"]]

                    for p, orig in zip(group["params"], original_params):
                        p.copy_(orig)

                r *= expand

            if best_params is not None:
                for p, best_p in zip(group["params"], best_params):
                    p.copy_(best_p)

        return loss
