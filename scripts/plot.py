import os
import pandas as pd
import matplotlib.pyplot as plt
import argparse

only_one = False

def load_mode_data(root_dir, mode_prefix=None):
    performance_data = []
    usage_data = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if (
                mode_prefix
                and file.startswith(mode_prefix)
                and "performance.csv" in file
            ):
                df_perf = pd.read_csv(os.path.join(root, file))
                performance_data.append(df_perf)
            elif not mode_prefix and "performance.csv" in file: 
                df_perf = pd.read_csv(os.path.join(root, file))
                performance_data.append(df_perf)
            if mode_prefix and file.startswith(mode_prefix) and "usage.csv" in file:
                df_usage = pd.read_csv(os.path.join(root, file))
                usage_data.append(df_usage)
            elif not mode_prefix and "usage.csv" in file:
                df_usage = pd.read_csv(os.path.join(root, file))
                usage_data.append(df_usage)
    if len(performance_data) == 1 or len(usage_data) == 1:
        global only_one
        only_one = True
    if performance_data:
        df_performance = (
            pd.concat(performance_data)
            .groupby("test")
            .agg(["mean", "std"])
            .reset_index()
        )
    else:
        df_performance = pd.DataFrame()

    if usage_data:
        df_usage = pd.concat(usage_data)
        df_usage_grouped = (
            df_usage.groupby("Metric")["Average"].agg(["mean", "std"]).reset_index()
        )
    else:
        df_usage_grouped = pd.DataFrame()

    return df_performance, df_usage_grouped


def extract_latency_statistics(performance_data):
    latency_columns = {
        "p50_latency": "p50_latency_ms",
        "p95_latency": "p95_latency_ms",
        "p99_latency": "p99_latency_ms",
        "avg_latency": "avg_latency_ms",
    }

    latencies = {}
    for key, col in latency_columns.items():
        if col in performance_data.columns:
            latencies[key] = performance_data[col]["mean"].mean()  
        else:
            latencies[key] = None
    return latencies


def plot_latency_statistics_comparison(
    rdb_perf, aof_perf, uring_perf, graphs_dir, name="latency_statistics_comparison"
):
    modes = ["RDB", "AOF (always)", "AOF (everysec)", "AOF (no)", "AOFUring"]
    colors = {
        "p50_latency": "green",
        "p95_latency": "orange",
        "p99_latency": "red",
        "avg_latency": "black",
    }

    latencies = {
        "RDB": extract_latency_statistics(rdb_perf),
        "AOF (always)": extract_latency_statistics(aof_perf["always"]),
        "AOF (everysec)": extract_latency_statistics(aof_perf["everysec"]),
        "AOF (no)": extract_latency_statistics(aof_perf["no"]),
        "AOFUring": extract_latency_statistics(uring_perf),
    }

    plt.figure(figsize=(12, 8))
    plt.clf()  

    for stat, color in colors.items():
        data_to_plot = [latencies[mode][stat] for mode in modes]
        plt.plot(
            modes,
            data_to_plot,
            marker="o",
            linestyle="-",
            color=color,
            label=stat,
        )

    plt.xlabel("Persistence Mode", fontsize=14, fontweight="bold")
    plt.ylabel("Latency (ms)", fontsize=14, fontweight="bold")  
    plt.xticks(range(len(modes)), modes, fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend(loc="upper left", fontsize=12)
    plt.tight_layout()

    plot_filename = os.path.join(graphs_dir, f"{name}.svg")
    plt.savefig(plot_filename, bbox_inches="tight", format="svg")


def load_all_data(aof_dir, rdb_dir, uring_dir):
    aof_modes = ["always", "everysec", "no"]
    aof_performance = {}
    aof_usage = {}

    for mode in aof_modes:
        aof_performance[mode], aof_usage[mode] = load_mode_data(
            aof_dir, mode_prefix=mode
        )

    rdb_performance, rdb_usage = load_mode_data(rdb_dir)
    uring_performance, uring_usage = load_mode_data(uring_dir)

    return (
        aof_performance,
        aof_usage,
        rdb_performance,
        rdb_usage,
        uring_performance,
        uring_usage,
    )


def plot_cpu_comparison_all(
    rdb_usage, aof_usage, uring_usage, graphs_dir, name="cpu_comparison"
):
    modes = ["RDB", "AOF (always)", "AOF (everysec)", "AOF (no)", "AOFUring"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    cpu_values = {
        "RDB": rdb_usage.loc[rdb_usage["Metric"] == "CPU Usage (%)", "mean"].values,
        "AOF (always)": aof_usage["always"]
        .loc[aof_usage["always"]["Metric"] == "CPU Usage (%)", "mean"]
        .values,
        "AOF (everysec)": aof_usage["everysec"]
        .loc[aof_usage["everysec"]["Metric"] == "CPU Usage (%)", "mean"]
        .values,
        "AOF (no)": aof_usage["no"]
        .loc[aof_usage["no"]["Metric"] == "CPU Usage (%)", "mean"]
        .values,
        "AOFUring": uring_usage.loc[
            uring_usage["Metric"] == "CPU Usage (%)", "mean"
        ].values,
    }

    cpu_std = {
        "RDB": rdb_usage.loc[rdb_usage["Metric"] == "CPU Usage (%)", "std"].values,
        "AOF (always)": aof_usage["always"]
        .loc[aof_usage["always"]["Metric"] == "CPU Usage (%)", "std"]
        .values,
        "AOF (everysec)": aof_usage["everysec"]
        .loc[aof_usage["everysec"]["Metric"] == "CPU Usage (%)", "std"]
        .values,
        "AOF (no)": aof_usage["no"]
        .loc[aof_usage["no"]["Metric"] == "CPU Usage (%)", "std"]
        .values,
        "AOFUring": uring_usage.loc[
            uring_usage["Metric"] == "CPU Usage (%)", "std"
        ].values,
    }

    plt.figure(figsize=(10, 6))
    if only_one:
        plt.bar(
            modes,
            [cpu_values[mode][0] for mode in modes],
            color=colors,
            capsize=5,
        )
    else:
        plt.bar(
            modes,
            [cpu_values[mode][0] for mode in modes],
            color=colors,
            yerr=[cpu_std[mode][0] for mode in modes],
            capsize=5,
        )

    plt.xlabel("Persistence Mode", fontsize=14, fontweight="bold")
    plt.ylabel("CPU Usage (%)", fontsize=14, fontweight="bold")
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(graphs_dir, f"{name}.svg")
    plt.savefig(plot_filename, bbox_inches="tight", format="svg")


def plot_memory_comparison_all(
    rdb_usage, aof_usage, uring_usage, graphs_dir, name="memory_comparison"
):
    modes = ["RDB", "AOF (always)", "AOF (everysec)", "AOF (no)", "AOFUring"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    memory_values = {
        "RDB": rdb_usage.loc[rdb_usage["Metric"] == "Memory Usage (MB)", "mean"].values,
        "AOF (always)": aof_usage["always"]
        .loc[aof_usage["always"]["Metric"] == "Memory Usage (MB)", "mean"]
        .values,
        "AOF (everysec)": aof_usage["everysec"]
        .loc[aof_usage["everysec"]["Metric"] == "Memory Usage (MB)", "mean"]
        .values,
        "AOF (no)": aof_usage["no"]
        .loc[aof_usage["no"]["Metric"] == "Memory Usage (MB)", "mean"]
        .values,
        "AOFUring": uring_usage.loc[
            uring_usage["Metric"] == "Memory Usage (MB)", "mean"
        ].values,
    }

    memory_std = {
        "RDB": rdb_usage.loc[rdb_usage["Metric"] == "Memory Usage (MB)", "std"].values,
        "AOF (always)": aof_usage["always"]
        .loc[aof_usage["always"]["Metric"] == "Memory Usage (MB)", "std"]
        .values,
        "AOF (everysec)": aof_usage["everysec"]
        .loc[aof_usage["everysec"]["Metric"] == "Memory Usage (MB)", "std"]
        .values,
        "AOF (no)": aof_usage["no"]
        .loc[aof_usage["no"]["Metric"] == "Memory Usage (MB)", "std"]
        .values,
        "AOFUring": uring_usage.loc[
            uring_usage["Metric"] == "Memory Usage (MB)", "std"
        ].values,
    }

    plt.figure(figsize=(10, 6))
    if only_one:
        plt.bar(
            modes,
            [memory_values[mode][0] for mode in modes],
            color=colors,
            capsize=5,
        )
    else:
        plt.bar(
            modes,
            [memory_values[mode][0] for mode in modes],
            yerr=[memory_std[mode][0] for mode in modes],
            color=colors,
            capsize=5,
        )
    plt.xlabel("Persistence Mode", fontsize=14, fontweight="bold")
    plt.ylabel("Memory Usage (MB)", fontsize=14, fontweight="bold")
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(graphs_dir, f"{name}.svg")
    plt.savefig(plot_filename, bbox_inches="tight", format="svg")


def plot_rps_comparison_all(
    rdb_perf, aof_perf, uring_perf, graphs_dir, name="rps_comparison"
):

    tests = rdb_perf["test"].values
    modes = ["RDB", "AOF (always)", "AOF (everysec)", "AOF (no)", "AOFUring"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    rps_values = {
        "RDB": rdb_perf.set_index("test")["rps"]["mean"].reindex(tests).values,
        "AOF (always)": aof_perf["always"]
        .set_index("test")["rps"]["mean"]
        .reindex(tests)
        .values,
        "AOF (everysec)": aof_perf["everysec"]
        .set_index("test")["rps"]["mean"]
        .reindex(tests)
        .values,
        "AOF (no)": aof_perf["no"]
        .set_index("test")["rps"]["mean"]
        .reindex(tests)
        .values,
        "AOFUring": uring_perf.set_index("test")["rps"]["mean"].reindex(tests).values,
    }

    rps_std = {
        "RDB": rdb_perf.set_index("test")["rps"]["std"].reindex(tests).values,
        "AOF (always)": aof_perf["always"]
        .set_index("test")["rps"]["std"]
        .reindex(tests)
        .values,
        "AOF (everysec)": aof_perf["everysec"]
        .set_index("test")["rps"]["std"]
        .reindex(tests)
        .values,
        "AOF (no)": aof_perf["no"]
        .set_index("test")["rps"]["std"]
        .reindex(tests)
        .values,
        "AOFUring": uring_perf.set_index("test")["rps"]["std"].reindex(tests).values,
    }

    x = range(len(tests))
    bar_width = 0.15

    plt.figure(figsize=(12, 8))

    if only_one:
        for i, mode in enumerate(modes):
            plt.bar(
                [p + i * bar_width for p in x],
                rps_values[mode],
                width=bar_width,
                label=mode,
                color=colors[i],
                capsize=5,
            )
    else:
        for i, mode in enumerate(modes):
            plt.bar(
                [p + i * bar_width for p in x],
                rps_values[mode],
                width=bar_width,
                yerr=rps_std[mode],
                label=mode,
                color=colors[i],
                capsize=5,
            )

    plt.xlabel("Redis Command", fontsize=14, fontweight="bold")
    plt.ylabel("Requests per Second (RPS)", fontsize=14, fontweight="bold")
    plt.xticks([p + 2 * bar_width for p in x], tests, fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    plt.legend(
        title="Persistence Mode",
        fontsize=12,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=3,
    )

    plt.tight_layout(rect=[0, 0, 1, 0.9])  

    plot_filename = os.path.join(graphs_dir, f"{name}.svg")
    plt.savefig(plot_filename, bbox_inches="tight", format="svg")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot graphs from CSV data.")
    parser.add_argument(
        "--dir_rdb", help="Directory containing RDB CSV files.", required=True
    )
    parser.add_argument(
        "--dir_aof", help="Directory containing AOF CSV files.", required=True
    )
    parser.add_argument(
        "--dir_uring", help="Directory containing URING_AOF CSV files.", required=True
    )
    parser.add_argument("--dir", help="Directory to save graphs.", default=".")
    parser.add_argument(
        "--type",
        choices=[
            "rps",
            "cpu",
            "memory",
            "latency",
            "all",
        ],
        help="Type of graph to plot.",
        required=True,
    )
    args = parser.parse_args()

    os.makedirs(args.dir, exist_ok=True)

    (
        aof_perf,
        aof_usage,
        rdb_perf,
        rdb_usage,
        uring_perf,
        uring_usage,
    ) = load_all_data(args.dir_aof, args.dir_rdb, args.dir_uring)

    if args.type == "rps":
        plot_rps_comparison_all(rdb_perf, aof_perf, uring_perf, args.dir)
    elif args.type == "cpu":
        plot_cpu_comparison_all(rdb_usage, aof_usage, uring_usage, args.dir)
    elif args.type == "memory":
        plot_memory_comparison_all(rdb_usage, aof_usage, uring_usage, args.dir)
    elif args.type == "latency":
        plot_latency_statistics_comparison(rdb_perf, aof_perf, uring_perf, args.dir)
    elif args.type == "all":
        plot_rps_comparison_all(rdb_perf, aof_perf, uring_perf, args.dir)
        plot_cpu_comparison_all(rdb_usage, aof_usage, uring_usage, args.dir)
        plot_memory_comparison_all(rdb_usage, aof_usage, uring_usage, args.dir)
        plot_latency_statistics_comparison(rdb_perf, aof_perf, uring_perf, args.dir)
