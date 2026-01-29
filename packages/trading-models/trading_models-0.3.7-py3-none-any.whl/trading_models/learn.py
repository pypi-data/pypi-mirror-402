import matplotlib.pyplot as plt
import numpy as np
import torch as tc
import torch.nn as nn
import torch.nn.functional as F
from crypto_data_downloader.utils import load_pkl, save_pkl
from fast_trading_simulator.sim import map_trades, simulate
from fast_trading_simulator.utils import make_market_n_obs, plot_act_hist

from trading_models.stat import StandardScaler
from trading_models.utils import (
    corr_coef,
    mlp,
    plot_general,
    shape,
    tensor,
    to_np,
    transpose_records,
)


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


# ==========================


class QFnLearner:
    def make_obs(s, path, periods, add_ref):
        s.market, s.obs = make_market_n_obs(path, periods=periods, add_ref_obs=add_ref)
        s.tot_fee = 1e-3
        s.liq_fee = np.full(len(s.obs), 0.02)

    def make_obs_act_pr(s, act_fn, clip_pr, plot=True):
        action = act_fn(s.obs)
        plot_act_hist(action) if plot else None
        trades = simulate(
            s.market,
            action,
            s.tot_fee,
            s.liq_fee,
            clip_pr=clip_pr,
            alloc_ratio=1e-3,
            init_cash=1e8,
        )
        res, (obs, act) = map_trades(trades, (s.obs, action), plot)
        pr = res["profit"][:, None]
        pr = np.minimum(pr, 0.2)
        print(shape((obs, act, pr)))
        save_pkl((obs, act, pr), "data/obs_act_pr.pkl")
        return obs, act, pr

    @staticmethod
    def safety_1st_loss(pr_pred, pr):
        SE = (pr_pred - pr) ** 2
        # pr < 0, pr_pred < 0 -> ok
        # pr < 0, pr_pred > 0 -> very bad
        # pr > 0, pr_pred < 0 -> bad
        # pr > 0, pr_pred > 0 -> ok
        very_bad = (pr < 0) & (pr_pred > 0)
        # bad = (pr > 0) & (pr_pred < 0)
        SE = tc.where(very_bad, SE * 100, SE)
        # SE = tc.where(bad, SE**2, SE)
        return SE.mean()

    def learn(s, obs_act_pr, net: nn.Module, loss_fn, lr=1e-3, steps=10000, f_plot=100):
        obs, act, pr = tensor(obs_act_pr)
        scaler = StandardScaler()
        obs_act = scaler.fit_transform(tc.concat((obs, act), dim=-1))
        opt = tc.optim.AdamW(net.parameters(), lr=lr)
        records = []
        for e in range(steps):
            pr_pred = net(obs_act)
            loss: tc.Tensor = loss_fn(pr_pred, pr)
            opt.zero_grad()
            loss.backward()
            opt.step()
            records.append(
                {"log10(loss)": np.log10(loss.item()), "corr": corr_coef(pr, pr_pred)}
            )
            print(records[-1])
            if e % f_plot == 0:
                s.plot(pr, pr_pred, records)

    def plot(s, pr, pr_pred, records, lim=[-0.5, 0.2]):
        plot_general(transpose_records(records), "data/QFnLearner_1")
        pr, pr_pred = to_np((pr, pr_pred))
        plt.scatter(pr, pr_pred, s=1, c="y", label="pr_pred")
        plt.plot(pr, pr, c="b", label="pr")
        plt.hlines(0, lim[0], lim[1], colors="k")
        plt.xlim(lim)
        plt.ylim(lim)
        plt.legend()
        plt.savefig("data/QFnLearner_2")
        plt.close()


def test_QFnLearner():
    s = QFnLearner()
    if 0:
        path = "futures_data_2025-08-01_2025-11-20.pkl"
        periods = [2**n for n in range(1, 10)]
        s.make_obs(path, periods, add_ref=False)

        def act_fn(obs: np.ndarray):
            SYM, TIME, _ = obs.shape
            size = (SYM, TIME, 1)
            pos = np.random.choice([-1, 1], size)
            lev = np.full(size, 1)
            timeout = np.full(size, 100)
            tp = np.full(size, 0.02)
            sl = np.full(size, -0.4)
            return np.concat((pos, lev, timeout, tp, sl), axis=-1)

        s.make_obs_act_pr(act_fn, clip_pr=False)
    else:
        obs_act_pr = load_pkl("data/obs_act_pr.pkl")
        net = mlp([9 + 5, 64, 64, 1])
        s.learn(obs_act_pr, net, s.safety_1st_loss)
