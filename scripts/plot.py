import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os


def plot_rps_comparison_all(
    df_rdb, df_aof, df_aofuring, graphs_dir, name="rps_comparison"
):
    labels = ["RDB", "AOF (always)", "AOF (everysec)", "AOF (no)", "AOFUring"]
    rps_values = [
        df_rdb["rps"].values[0],
        df_aof[df_aof["Fsync Type"] == "always"]["rps"].values[0],
        df_aof[df_aof["Fsync Type"] == "everysec"]["rps"].values[0],
        df_aof[df_aof["Fsync Type"] == "no"]["rps"].values[0],
        df_aofuring["rps"].values[0],
    ]
    colors = ["green", "blue", "#1E90FF", "#4169E1", "red"]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, rps_values, color=colors, edgecolor="black", linewidth=1.5)

    for bar in bars:
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 500,
            f"{int(bar.get_height()):,}",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

    plt.xlabel("Persistence Mode", fontsize=14, fontweight="bold")
    plt.ylabel("Requests per Second (RPS)", fontsize=14, fontweight="bold")
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(graphs_dir, f"{name}.svg")
    plt.savefig(plot_filename, bbox_inches="tight", format="svg")


def plot_syscalls_comparison_all(
    df_rdb, df_aof, df_aofuring, graphs_dir, name="syscalls_comparison"
):
    labels = ["fdatasync", "write", "io_uring_enter"]
    syscalls_rdb = [
        df_rdb["fdatasync_count"].values[0],
        df_rdb["write_count"].values[0],
        df_rdb["io_uring_enter_count"].values[0],
    ]
    syscalls_aof_always = [
        df_aof[df_aof["Fsync Type"] == "always"]["fdatasync_count"].values[0],
        df_aof[df_aof["Fsync Type"] == "always"]["write_count"].values[0],
        df_aof[df_aof["Fsync Type"] == "always"]["io_uring_enter_count"].values[0],
    ]
    syscalls_aof_everysec = [
        df_aof[df_aof["Fsync Type"] == "everysec"]["fdatasync_count"].values[0],
        df_aof[df_aof["Fsync Type"] == "everysec"]["write_count"].values[0],
        df_aof[df_aof["Fsync Type"] == "everysec"]["io_uring_enter_count"].values[0],
    ]
    syscalls_aof_no = [
        df_aof[df_aof["Fsync Type"] == "no"]["fdatasync_count"].values[0],
        df_aof[df_aof["Fsync Type"] == "no"]["write_count"].values[0],
        df_aof[df_aof["Fsync Type"] == "no"]["io_uring_enter_count"].values[0],
    ]
    syscalls_aofuring = [
        df_aofuring["fdatasync_count"].values[0],
        df_aofuring["write_count"].values[0],
        df_aofuring["io_uring_enter_count"].values[0],
    ]

    x = range(len(labels))
    bar_width = 0.15

    plt.figure(figsize=(12, 8))
    plt.bar(
        [p - 2 * bar_width for p in x],
        syscalls_rdb,
        width=bar_width,
        label="RDB",
        color="green",
    )
    plt.bar(
        [p - bar_width for p in x],
        syscalls_aof_always,
        width=bar_width,
        label="AOF (always)",
        color="blue",
    )
    plt.bar(
        x,
        syscalls_aof_everysec,
        width=bar_width,
        label="AOF (everysec)",
        color="#1E90FF",
    )
    plt.bar(
        [p + bar_width for p in x],
        syscalls_aof_no,
        width=bar_width,
        label="AOF (no)",
        color="#4169E1",
    )
    plt.bar(
        [p + 2 * bar_width for p in x],
        syscalls_aofuring,
        width=bar_width,
        label="AOFUring",
        color="red",
    )

    plt.xlabel("System Call", fontsize=14, fontweight="bold")
    plt.ylabel("Number of Calls", fontsize=14, fontweight="bold")
    plt.xticks(x, labels, rotation=0, fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(loc="upper right", fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(graphs_dir, f"{name}.svg")
    plt.savefig(plot_filename, bbox_inches="tight", format="svg")


def plot_cpu_comparison_all(
    df_rdb, df_aof, df_aofuring, graphs_dir, name="cpu_comparison"
):
    labels = ["RDB", "AOF (always)", "AOF (everysec)", "AOF (no)", "AOFUring"]
    cpu_values = [
        df_rdb["CPU Usage"].values[0],
        df_aof[df_aof["Fsync Type"] == "always"]["CPU Usage"].values[0],
        df_aof[df_aof["Fsync Type"] == "everysec"]["CPU Usage"].values[0],
        df_aof[df_aof["Fsync Type"] == "no"]["CPU Usage"].values[0],
        df_aofuring["CPU Usage"].values[0],
    ]
    colors = ["green", "blue", "#1E90FF", "#4169E1", "red"]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, cpu_values, color=colors, edgecolor="black", linewidth=1.5)

    for bar in bars:
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{bar.get_height():.2f}%",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
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
    df_rdb, df_aof, df_aofuring, graphs_dir, name="memory_comparison"
):
    labels = ["RDB", "AOF (always)", "AOF (everysec)", "AOF (no)", "AOFUring"]
    memory_values = [
        df_rdb["Memory Usage"].values[0],
        df_aof[df_aof["Fsync Type"] == "always"]["Memory Usage"].values[0],
        df_aof[df_aof["Fsync Type"] == "everysec"]["Memory Usage"].values[0],
        df_aof[df_aof["Fsync Type"] == "no"]["Memory Usage"].values[0],
        df_aofuring["Memory Usage"].values[0],
    ]
    colors = ["green", "blue", "#1E90FF", "#4169E1", "red"]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(
        labels, memory_values, color=colors, edgecolor="black", linewidth=1.5
    )

    for bar in bars:
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            f"{bar.get_height():.2f} MB",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

    plt.xlabel("Persistence Mode", fontsize=14, fontweight="bold")
    plt.ylabel("Memory Usage (MB)", fontsize=14, fontweight="bold")
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(graphs_dir, f"{name}.svg")
    plt.savefig(plot_filename, bbox_inches="tight", format="svg")


def plot_latency_comparison_all(
    df_rdb, df_aof, df_aofuring, graphs_dir, name="latency_comparison"
):
    labels = ["RDB", "AOF (always)", "AOF (everysec)", "AOF (no)", "AOFUring"]

    colors = ["green", "blue", "#1E90FF", "#4169E1", "red"]

    latencies = [
        df_rdb[
            [
                "avg_latency_ms",
                "min_latency_ms",
                "p50_latency_ms",
                "p95_latency_ms",
                "p99_latency_ms",
                "max_latency_ms",
            ]
        ].values.flatten(),
        df_aof[df_aof["Fsync Type"] == "always"][
            [
                "avg_latency_ms",
                "min_latency_ms",
                "p50_latency_ms",
                "p95_latency_ms",
                "p99_latency_ms",
                "max_latency_ms",
            ]
        ].values.flatten(),
        df_aof[df_aof["Fsync Type"] == "everysec"][
            [
                "avg_latency_ms",
                "min_latency_ms",
                "p50_latency_ms",
                "p95_latency_ms",
                "p99_latency_ms",
                "max_latency_ms",
            ]
        ].values.flatten(),
        df_aof[df_aof["Fsync Type"] == "no"][
            [
                "avg_latency_ms",
                "min_latency_ms",
                "p50_latency_ms",
                "p95_latency_ms",
                "p99_latency_ms",
                "max_latency_ms",
            ]
        ].values.flatten(),
        df_aofuring[
            [
                "avg_latency_ms",
                "min_latency_ms",
                "p50_latency_ms",
                "p95_latency_ms",
                "p99_latency_ms",
                "max_latency_ms",
            ]
        ].values.flatten(),
    ]

    plt.figure(figsize=(12, 8))

    boxprops = dict(linewidth=3, color="black")
    medianprops = dict(linewidth=4, color="white")  
    whiskerprops = dict(linewidth=3)
    capprops = dict(linewidth=3)

    boxplot = plt.boxplot(
        latencies,
        labels=labels,
        patch_artist=True,
        showfliers=True, 
        boxprops=boxprops,
        medianprops=medianprops,
        whiskerprops=whiskerprops,
        capprops=capprops,
    )

    for patch, color in zip(boxplot["boxes"], colors):
        patch.set_facecolor(color)

    medians = [item.get_ydata()[0] for item in boxplot["medians"]]
    for i, median in enumerate(medians):
        plt.text(
            i + 1,
            median,
            f"{median:.2f}",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
            color="black",
        )

    plt.yscale("log")
    plt.xlabel("Persistence Mode", fontsize=16, fontweight="bold")
    plt.ylabel("Latency (ms) [Log Scale]", fontsize=16, fontweight="bold")
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(graphs_dir, f"{name}.svg")
    plt.savefig(plot_filename, bbox_inches="tight", format="svg")


import pandas as pd
import matplotlib.pyplot as plt
import os


import pandas as pd
import matplotlib.pyplot as plt
import os


def create_syscall_times_table(
    df_rdb, df_aof, df_aofuring, graphs_dir, name="syscall_times_table"
):
    def to_milliseconds(time_series):
        return time_series * 1000

    syscall_times_rdb = to_milliseconds(
        df_rdb[["write_time", "fdatasync_time", "io_uring_enter_time", "total_time"]]
    )
    syscall_times_aof_always = to_milliseconds(
        df_aof[df_aof["Fsync Type"] == "always"][
            ["write_time", "fdatasync_time", "io_uring_enter_time", "total_time"]
        ]
    )
    syscall_times_aof_everysec = to_milliseconds(
        df_aof[df_aof["Fsync Type"] == "everysec"][
            ["write_time", "fdatasync_time", "io_uring_enter_time", "total_time"]
        ]
    )
    syscall_times_aof_no = to_milliseconds(
        df_aof[df_aof["Fsync Type"] == "no"][
            ["write_time", "fdatasync_time", "io_uring_enter_time", "total_time"]
        ]
    )
    syscall_times_aofuring = to_milliseconds(
        df_aofuring[
            ["write_time", "fdatasync_time", "io_uring_enter_time", "total_time"]
        ]
    )

    combined_data = pd.DataFrame(
        {
            "System Call": ["write", "fdatasync", "io_uring_enter", "total"],
            "RDB": syscall_times_rdb.values.flatten(),
            "AOF (always)": syscall_times_aof_always.values.flatten(),
            "AOF (everysec)": syscall_times_aof_everysec.values.flatten(),
            "AOF (no)": syscall_times_aof_no.values.flatten(),
            "AOFUring": syscall_times_aofuring.values.flatten(),
        }
    )

    fig, ax = plt.subplots(figsize=(8, 3)) 
    ax.axis("tight")
    ax.axis("off")
    table = ax.table(
        cellText=combined_data.values,
        colLabels=combined_data.columns,
        cellLoc="center",
        loc="center",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)  

    plot_filename = os.path.join(graphs_dir, f"{name}.svg")
    plt.savefig(plot_filename, bbox_inches="tight", format="svg")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot graphs from CSV data.")
    parser.add_argument("--csv_rdb", help="Path to RDB CSV file.", required=True)
    parser.add_argument("--csv_aof", help="Path to AOF CSV file.", required=True)
    parser.add_argument(
        "--csv_aofuring", help="Path to AOFUring CSV file.", required=True
    )
    parser.add_argument("--dir", help="Directory to save graphs.", default=".")
    parser.add_argument(
        "--type",
        choices=["rps", "syscalls", "cpu", "memory", "all", "latency", "syscall_times"],
        help="Type of graph to plot.",
        required=True,
    )
    args = parser.parse_args()

    os.makedirs(args.dir, exist_ok=True)

    df_rdb = pd.read_csv(args.csv_rdb)
    df_aof = pd.read_csv(args.csv_aof)
    df_aofuring = pd.read_csv(args.csv_aofuring)

    if args.type == "rps":
        plot_rps_comparison_all(df_rdb, df_aof, df_aofuring, args.dir)
    elif args.type == "syscalls":
        plot_syscalls_comparison_all(df_rdb, df_aof, df_aofuring, args.dir)
    elif args.type == "cpu":
        plot_cpu_comparison_all(df_rdb, df_aof, df_aofuring, args.dir)
    elif args.type == "memory":
        plot_memory_comparison_all(df_rdb, df_aof, df_aofuring, args.dir)
    elif args.type == "latency":
        plot_latency_comparison_all(df_rdb, df_aof, df_aofuring, args.dir)
    elif args.type == "syscall_times":
        create_syscall_times_table(df_rdb, df_aof, df_aofuring, args.dir)
    elif args.type == "all":
        plot_rps_comparison_all(df_rdb, df_aof, df_aofuring, args.dir)
        plot_syscalls_comparison_all(df_rdb, df_aof, df_aofuring, args.dir)
        plot_cpu_comparison_all(df_rdb, df_aof, df_aofuring, args.dir)
        plot_memory_comparison_all(df_rdb, df_aof, df_aofuring, args.dir)
        plot_latency_comparison_all(df_rdb, df_aof, df_aofuring, args.dir)
        create_syscall_times_table(df_rdb, df_aof, df_aofuring, args.dir)
