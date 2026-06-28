"""
Generates all plots and saves them to outputs/plots/.
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns

plots_dir = "outputs/plots"


def plot_responder_boxplots(df, stats_df):
    """
    Part 3: boxplot of cell population frequencies for
    responders vs non-responders, one panel per population.
    """
    os.makedirs(plots_dir, exist_ok=True)

    populations = sorted(df["population"].unique())
    n = len(populations)

    fig, axes = plt.subplots(1, n, figsize=(4 * n, 5), sharey=False)

    # map p-values for annotation
    p_values = stats_df.set_index("population")["p_value"].to_dict()

    palette = {"yes": "#2ecc71", "no": "#e74c3c"}

    for ax, pop in zip(axes, populations):
        subset = df[df["population"] == pop]

        sns.boxplot(
            data=subset,
            x="response",
            y="percentage",
            hue="response",
            palette=palette,
            order=["yes", "no"],
            width=0.5,
            legend=False,
            ax=ax,
        )
        sns.stripplot(
            data=subset,
            x="response",
            y="percentage",
            color="black",
            size=3,
            jitter=True,
            order=["yes", "no"],
            ax=ax,
        )

        # annotate with p-value and star if significant
        p = p_values.get(pop, None)
        star = " *" if p is not None and p < 0.05 else ""
        ax.set_title(f"{pop}{star}\np = {p:.4f}", fontsize=10)
        ax.set_xlabel("")
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Responder", "Non-responder"], fontsize=8)
        ax.set_ylabel("Frequency (%)" if pop == populations[0] else "")

    fig.suptitle(
        "Cell Population Frequencies: Responders vs Non-Responders\n"
        "(Melanoma · Miraclib · PBMC)",
        fontsize=12,
    )
    plt.tight_layout()

    out = os.path.join(plots_dir, "responder_boxplots.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")