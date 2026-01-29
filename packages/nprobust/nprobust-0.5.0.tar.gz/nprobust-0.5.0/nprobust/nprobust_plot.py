"""
Plotting Functions for nprobust.

This module implements plotting functions for visualizing
local polynomial regression and kernel density estimation results.
"""

import numpy as np
from scipy import stats

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def nprobust_plot(*args, alpha=None, plot_type=None, ci_type=None,
                  title="", xlabel="", ylabel="",
                  lty=None, lwd=None, lcol=None, pty=None, pwd=None, pcol=None,
                  ci_shade=None, ci_col=None, legend_title=None, legend_groups=None,
                  figsize=(10, 6)):
    """
    Plot nprobust estimation results.

    Parameters
    ----------
    *args : LprobustResult or KdrobustResult
        One or more result objects to plot.
    alpha : float or list
        Significance level(s) for confidence intervals. Default is 0.05.
    plot_type : str or list
        Plot type(s): 'line', 'points', 'both'. Default is 'line'.
    ci_type : str or list
        CI type(s): 'region', 'line', 'ebar', 'all', 'none'. Default is 'region'.
    title : str
        Plot title.
    xlabel : str
        X-axis label.
    ylabel : str
        Y-axis label.
    lty : int or list
        Line style(s).
    lwd : float or list
        Line width(s).
    lcol : str or list
        Line color(s).
    pty : int or list
        Point style(s).
    pwd : float or list
        Point size(s).
    pcol : str or list
        Point color(s).
    ci_shade : float or list
        CI shade alpha(s).
    ci_col : str or list
        CI color(s).
    legend_title : str
        Legend title.
    legend_groups : list
        Legend group names.
    figsize : tuple
        Figure size (width, height).

    Returns
    -------
    matplotlib.figure.Figure
        The matplotlib figure object.
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required for plotting. Install with: pip install matplotlib")

    nfig = len(args)
    if nfig == 0:
        raise ValueError("Nothing to plot.")

    # Set defaults
    if alpha is None:
        alpha = [0.05] * nfig
    elif np.isscalar(alpha):
        alpha = [alpha] * nfig
    else:
        alpha = list(alpha) * (nfig // len(alpha) + 1)
        alpha = alpha[:nfig]

    if plot_type is None:
        plot_type = ["line"] * nfig
    elif isinstance(plot_type, str):
        plot_type = [plot_type] * nfig
    else:
        plot_type = list(plot_type) * (nfig // len(plot_type) + 1)
        plot_type = plot_type[:nfig]

    if ci_type is None:
        ci_type = ["region"] * nfig
    elif isinstance(ci_type, str):
        ci_type = [ci_type] * nfig
    else:
        ci_type = list(ci_type) * (nfig // len(ci_type) + 1)
        ci_type = ci_type[:nfig]

    # Line styles
    if lty is None:
        lty = ['-'] * nfig
    elif isinstance(lty, (int, str)):
        lty = [lty] * nfig
    else:
        lty = list(lty) * (nfig // len(lty) + 1)
        lty = lty[:nfig]

    if lwd is None:
        lwd = [1.5] * nfig
    elif np.isscalar(lwd):
        lwd = [lwd] * nfig
    else:
        lwd = list(lwd) * (nfig // len(lwd) + 1)
        lwd = lwd[:nfig]

    # Default colors
    default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    if lcol is None:
        lcol = [default_colors[i % len(default_colors)] for i in range(nfig)]
    elif isinstance(lcol, str):
        lcol = [lcol] * nfig
    else:
        lcol = list(lcol) * (nfig // len(lcol) + 1)
        lcol = lcol[:nfig]

    # Point styles
    if pty is None:
        pty = ['o'] * nfig
    elif isinstance(pty, (int, str)):
        pty = [pty] * nfig
    else:
        pty = list(pty) * (nfig // len(pty) + 1)
        pty = pty[:nfig]

    if pwd is None:
        pwd = [5] * nfig
    elif np.isscalar(pwd):
        pwd = [pwd] * nfig
    else:
        pwd = list(pwd) * (nfig // len(pwd) + 1)
        pwd = pwd[:nfig]

    if pcol is None:
        pcol = lcol
    elif isinstance(pcol, str):
        pcol = [pcol] * nfig
    else:
        pcol = list(pcol) * (nfig // len(pcol) + 1)
        pcol = pcol[:nfig]

    # CI styles
    if ci_shade is None:
        ci_shade = [0.2] * nfig
    elif np.isscalar(ci_shade):
        ci_shade = [ci_shade] * nfig
    else:
        ci_shade = list(ci_shade) * (nfig // len(ci_shade) + 1)
        ci_shade = ci_shade[:nfig]

    if ci_col is None:
        ci_col = lcol
    elif isinstance(ci_col, str):
        ci_col = [ci_col] * nfig
    else:
        ci_col = list(ci_col) * (nfig // len(ci_col) + 1)
        ci_col = ci_col[:nfig]

    # Legend
    if legend_title is None:
        legend_title = ""

    if legend_groups is None:
        legend_groups = [f"Series {i+1}" for i in range(nfig)]
    else:
        legend_groups = list(legend_groups) * (nfig // len(legend_groups) + 1)
        legend_groups = legend_groups[:nfig]

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    for i in range(nfig):
        result = args[i]
        data = result.Estimate

        eval_pts = data[:, 0]
        tau_us = data[:, 4]
        tau_bc = data[:, 5]
        se_rb = data[:, 7]

        z_val = stats.norm.ppf(1 - alpha[i] / 2)
        CI_l = tau_bc - z_val * se_rb
        CI_r = tau_bc + z_val * se_rb

        # Sort by evaluation points for proper line plotting
        sort_idx = np.argsort(eval_pts)
        eval_pts = eval_pts[sort_idx]
        tau_us = tau_us[sort_idx]
        CI_l = CI_l[sort_idx]
        CI_r = CI_r[sort_idx]

        # Plot CI region
        if ci_type[i] in ["region", "all"]:
            ax.fill_between(eval_pts, CI_l, CI_r, alpha=ci_shade[i],
                           color=ci_col[i], linewidth=0)

        # Plot CI lines
        if ci_type[i] in ["line", "all"]:
            ax.plot(eval_pts, CI_l, linestyle='--', alpha=0.5,
                   color=ci_col[i], linewidth=lwd[i] * 0.7)
            ax.plot(eval_pts, CI_r, linestyle='--', alpha=0.5,
                   color=ci_col[i], linewidth=lwd[i] * 0.7)

        # Plot CI error bars
        if ci_type[i] in ["ebar", "all"]:
            ax.errorbar(eval_pts, tau_us, yerr=[tau_us - CI_l, CI_r - tau_us],
                       fmt='none', alpha=ci_shade[i], color=ci_col[i], capsize=3)

        # Plot lines
        if plot_type[i] in ["line", "both"]:
            ax.plot(eval_pts, tau_us, linestyle=lty[i], linewidth=lwd[i],
                   color=lcol[i], label=legend_groups[i])

        # Plot points
        if plot_type[i] in ["points", "both"]:
            ax.scatter(eval_pts, tau_us, marker=pty[i], s=pwd[i]**2,
                      color=pcol[i], label=legend_groups[i] if plot_type[i] == "points" else None)

    # Labels and legend
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    if nfig > 1 or legend_groups[0] != "Series 1":
        ax.legend(title=legend_title)

    plt.tight_layout()

    return fig
