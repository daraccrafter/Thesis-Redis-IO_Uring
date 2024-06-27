import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os


def plot_boxplot(
    df,
    graphs_dir,
    name="",
    color="blue",
    avg_color="black",  
):
    data = []
    labels = []

    for _, row in df.iterrows():
        test_name = row["test"]
        latencies = row[
            [
                "avg_latency_ms",
                "min_latency_ms",
                "p50_latency_ms",
                "p95_latency_ms",
                "p99_latency_ms",
                "max_latency_ms",
            ]
        ].values
        data.append(latencies)
        labels.append(test_name)

    plt.figure(figsize=(10, 6))
    box = plt.boxplot(
        data,
        labels=labels,
        patch_artist=True,
        medianprops=dict(color=avg_color, linewidth=2.5),
    )

    for item in box["boxes"]:
        item.set(color=color, linewidth=2)
        item.set(facecolor=color)

    plt.ylabel("Latency (ms)", fontsize=12)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plot_filename = os.path.join(graphs_dir, f"{name}.svg")
    plt.savefig(plot_filename, bbox_inches="tight", format="svg")
    plt.close()


def plot_syscalls_comparison(
    df_avg_1,
    df_avg_2,
    graphs_dir,
    label_1="Label 1",
    label_2="Label 2",
    bar_1_color="blue",
    bar_2_color="red",
    name="",
):
    labels = df_avg_1["syscall"]
    syscalls_1 = df_avg_1["avg_count"]
    syscalls_2 = df_avg_2["avg_count"]
    x = range(len(labels))
    bar_width = 0.35
    plt.figure(figsize=(10, 6))
    bar_positions_1 = [p - bar_width / 2 for p in x]
    bar_positions_2 = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_1,
        syscalls_1,
        width=bar_width,
        label=label_1,
        color=bar_1_color,
    )
    plt.bar(
        bar_positions_2,
        syscalls_2,
        width=bar_width,
        label=label_2,
        color=bar_2_color,
    )
    plt.xlabel("Systemcall", fontsize=12)
    plt.ylabel("Average number of calls", fontsize=12)
    combined_positions = [
        (bar_positions_1[i] + bar_positions_2[i]) / 2 for i in range(len(labels))
    ]
    plt.xticks(ticks=combined_positions, labels=labels, rotation=0)
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plot_filename = os.path.join(
        graphs_dir, f"{name}.svg"
    )
    plt.savefig(plot_filename, bbox_inches="tight",format='svg')
    plt.close()


def plot_cpu_comparison(
    df_avg_1,
    df_avg_2,
    graphs_dir,
    label_1="Label 1",
    label_2="Label 2",
    bar_1_color="blue",
    bar_2_color="red",
    name="",
):
    labels = ["CPU Usage"]
    cpu_1 = [df_avg_1[0]]
    cpu_2 = [df_avg_2[0]]
    x = range(len(labels))
    bar_width = 0.35
    plt.figure(figsize=(4, 6))
    bar_positions_1 = [p - bar_width / 2 for p in x]
    bar_positions_2 = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_1,
        cpu_1,
        width=bar_width,
        label=label_1,
        color=bar_1_color,
    )
    plt.bar(
        bar_positions_2,
        cpu_2,
        width=bar_width,
        label=label_2,
        color=bar_2_color,
    )
    plt.ylabel("Average CPU usage (%)", fontsize=12)

    plt.xticks([])
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=1)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plot_filename = os.path.join(
        graphs_dir, f"{name}.svg"
    )
    plt.savefig(plot_filename, bbox_inches="tight",format='svg')
    plt.close()


def plot_memory_comparison(
    df_avg_1,
    df_avg_2,
    graphs_dir,
    label_1="Label 1",
    label_2="Label 2",
    bar_1_color="blue",
    bar_2_color="red",
    name="",
):
    labels = ["Memory Usage"]
    memory_1 = [df_avg_1[1]]
    memory_2 = [df_avg_2[1]]

    x = range(len(labels))
    bar_width = 0.05

    plt.figure(figsize=(4, 6))

    bar_positions_1 = [p - bar_width / 2 for p in x]
    bar_positions_2 = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_1,
        memory_1,
        width=bar_width,
        label=label_1,
        color=bar_1_color,
    )
    plt.bar(
        bar_positions_2,
        memory_2,
        width=bar_width,
        label=label_2,
        color=bar_2_color,
    )

    plt.xticks([])
    plt.ylabel("Average memory usage (MB)", fontsize=12)

    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=1)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plot_filename = os.path.join(
        graphs_dir, f"{name}.svg"
    )
    plt.savefig(plot_filename, bbox_inches="tight",format='svg')
    plt.close()


def plot_syscall_times_comparison(
    df_avg_1,
    df_avg_2,
    graphs_dir,
    label_1="Label 1",
    label_2="Label 2",
    bar_1_color="blue",
    bar_2_color="red",
    name="",
):
    labels = df_avg_1["syscall"]
    syscalls_1 = df_avg_1["avg_time"]  # Keep in seconds
    syscalls_2 = df_avg_2["avg_time"]  # Keep in seconds
    x = range(len(labels))
    bar_width = 0.35
    plt.figure(figsize=(10, 6))
    bar_positions_1 = [p - bar_width / 2 for p in x]
    bar_positions_2 = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_1,
        syscalls_1,
        width=bar_width,
        label=label_1,
        color=bar_1_color,
    )
    plt.bar(
        bar_positions_2,
        syscalls_2,
        width=bar_width,
        label=label_2,
        color=bar_2_color,
    )
    plt.xlabel("Systemcall", fontsize=12)
    plt.ylabel("Average latency [s]", fontsize=12)
    plt.yscale("log")
    combined_positions = [
        (bar_positions_1[i] + bar_positions_2[i]) / 2 for i in range(len(labels))
    ]
    plt.xticks(ticks=combined_positions, labels=labels, rotation=0)
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plot_filename = os.path.join(
        graphs_dir, f"{name}.svg"
    )
    plt.savefig(plot_filename, bbox_inches="tight",format='svg')
    plt.close()


def plot_rps_comparison(
    df_avg_1,
    df_avg_2,
    graphs_dir,
    label_1="Label 1",
    label_2="Label 2",
    bar_1_color="blue",
    bar_2_color="red",
    name="" 
):
    labels = df_avg_1["test"]
    rps_1 = df_avg_1["rps"]
    rps_2 = df_avg_2["rps"]
    x = range(len(labels))
    bar_width = 0.35
    plt.figure(figsize=(8, 6))
    bar_positions_1 = [p - bar_width / 2 for p in x]
    bar_positions_2 = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_1,
        rps_1,
        width=bar_width,
        label=label_1,
        color=bar_1_color,
    )
    plt.bar(
        bar_positions_2,
        rps_2,
        width=bar_width,
        label=label_2,
        color=bar_2_color,
    )
    plt.xlabel("Operation", fontsize=12)
    plt.ylabel("Requests per second (RPS)", fontsize=12)
    combined_positions = [
        (bar_positions_1[i] + bar_positions_2[i]) / 2 for i in range(len(labels))
    ]
    plt.xticks(ticks=combined_positions, labels=labels, rotation=0)
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plot_filename = os.path.join(
        graphs_dir, f"{name}.svg"
    )
    plt.savefig(plot_filename, bbox_inches="tight",format='svg')
    plt.close()

if __name__ == "__main__":
        parser = argparse.ArgumentParser(description="Plot graphs from CSV data.")
        parser.add_argument("--gt", help="Type of graph to plot. Options: syscall, syscalltime, rps, cpu, mem, perc")
        parser.add_argument("--csv1", help="Path to first CSV file.")
        parser.add_argument("--csv2", help="Path to second CSV file.")
        parser.add_argument("--dir", help="Directory to save graph.",default=".")
        parser.add_argument("--l1", help="Label for first dataset.",default="Label 1")
        parser.add_argument("--l2", help="Label for second dataset.",default="Label 2")
        parser.add_argument("--c1", help="Color for first dataset bars.",default="blue")
        parser.add_argument("--c2", help="Color for second dataset bars.",default="red")
        parser.add_argument("--name", help="Name of the graph file.",default="")
        args = parser.parse_args()
        print("here")
        if(args.gt == "perc"):
            df = pd.read_csv(args.csv1)
        else:
            df_avg_1 = pd.read_csv(args.csv1)
            df_avg_2 = pd.read_csv(args.csv2)
        if args.name == "":
            if(args.gt == "percentiles"):
                csv1_name = os.path.splitext(os.path.basename(args.csv1))[0]
                args.name= f"{args.gt}_{csv1_name}"
            else:
                csv1_name = os.path.splitext(os.path.basename(args.csv1))[0]
                csv2_name = os.path.splitext(os.path.basename(args.csv2))[0]
                args.name = f"{args.gt}_{csv1_name}_vs_{csv2_name}"
        if args.gt == "syscall":
            plot_syscalls_comparison(df_avg_1, df_avg_2, args.dir, args.l1, args.l2, args.c1, args.c2,args.name)
        elif args.gt == "syscalltime":
            plot_syscall_times_comparison(df_avg_1, df_avg_2,  args.dir, args.l1, args.l2, args.c1, args.c2,args.name)
        elif args.gt == "rps":
            plot_rps_comparison(df_avg_1, df_avg_2, args.dir, args.l1, args.l2, args.c1, args.c2,args.name)
        elif args.gt == "cpu":
            plot_cpu_comparison(df_avg_1, df_avg_2, args.dir, args.l1, args.l2, args.c1, args.c2,args.name)
        elif args.gt == "mem":
            plot_memory_comparison(df_avg_1, df_avg_2, args.dir, args.l1, args.l2, args.c1, args.c2,args.name)
        elif args.gt == "perc":
            plot_boxplot(df, args.dir, args.name, args.c1)
        print(f"Saved plot at {args.dir}/{args.name}.svg")
