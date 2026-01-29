import torch as tc
import torch.nn as nn
import torch.nn.functional as F

from trading_models.utils import plot_general


def learn_uniform_act(
    net: nn.Module, obs, targ_loss=1e-3, lr=1e-3, steps=1000, f_save=20
):
    opt = tc.optim.Adam(net.parameters(), lr=lr)
    for e in range(steps):
        act = tc.tanh(net(obs))
        act = act.view(-1, act.size(-1))
        B, D = act.shape
        act, _ = tc.sort(act, dim=0)
        target = tc.linspace(-0.99, 0.99, B).unsqueeze(1).expand(B, D)
        loss = F.mse_loss(act, target)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if e % f_save == 0 or e == steps - 1:
            print(f"{e}, loss: {loss.item():.6f}")
            plots = {}
            for i in range(D):
                plots[f"act_{i}_hist"] = act[:, i]
                plots[f"act_{i}*_hist"] = target[:, i]
            plot_general(plots, "act_hist")
            tc.save(net.state_dict(), "uniform_act.tc")
            if loss < targ_loss:
                break
