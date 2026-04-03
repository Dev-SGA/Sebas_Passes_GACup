import streamlit as st
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import pandas as pd
import numpy as np
from PIL import Image
from io import BytesIO
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

# Novas coordenadas (Sucessos seguidos de Falhas para cada partida)
coords_by_match = {
    'Vs Los Angeles': [
        # Sucesso (1 ao 3)
        (52.52, 13.90), (78.12, 72.42),
        (98.73, 43.66), (90.42, 36.84),
        (105.55, 22.38), (99.23, 48.98),
        # Falha (4 ao 8)
        (72.63, 9.41), (93.08, 18.06),
        (105.38, 18.06), (108.37, 30.69),
        (105.05, 48.15), (100.89, 40.33),
        (99.06, 56.96), (116.52, 65.43),
        (42.21, 41.99), (49.19, 54.13)
    ],
    'Vs Slavia Praha': [
        # Sucesso (1 ao 4)
        (91.25, 28.53), (100.73, 19.39),
        (95.91, 27.03), (104.72, 16.89),
        (103.55, 21.05), (101.23, 45.98),
        (85.60, 53.63), (91.42, 59.12),
        # Falha (5 ao 7)
        (119.68, 21.55), (111.86, 37.84),
        (94.58, 27.03), (101.39, 22.88),
        (117.52, 67.59), (105.22, 25.37)
    ],
    'Vs Sockers': [
        # Sucesso (1 ao 4)
        (114.36, 66.93), (104.38, 42.83),
        (70.97, 30.19), (77.79, 41.33),
        (64.49, 35.35), (71.47, 52.63),
        (51.52, 26.87), (65.15, 21.05),
        # Falha (5 ao 7)
        (110.37, 13.90), (114.03, 46.32),
        (93.25, 73.08), (109.21, 42.83),
        (79.28, 3.59), (95.24, 36.51)
    ]
}

# Índices (1-based) dos passes que resultaram em falha em cada partida
passes_errados_by_match = {
    'Vs Los Angeles': [4, 5, 6, 7, 8],
    'Vs Slavia Praha': [5, 6, 7],
    'Vs Sockers': [5, 6, 7]
}

st.set_page_config(layout="wide", page_title="Pass Map Dashboard")
st.title("Pass Map Dashboard")

# ==========================
# Configuration
# ==========================
GOAL_X = 120
GOAL_Y = 40
FINAL_THIRD_LINE_X = 80  # entry: start outside (x < 80) and end inside (x >= 80)

MATCHES = ["Vs Los Angeles", "Vs Slavia Praha", "Vs Sockers", "All Matches"]

st.sidebar.header("Match selection")
selected_match = st.sidebar.radio("Choose the match", MATCHES, index=0)

st.sidebar.header("Pass filter")
pass_filter = st.sidebar.radio(
    "Filter passes",
    ["All Passes", "Successful Only", "Unsuccessful Only"],
    index=0
)


def build_df(coords: list[tuple[float, float]], passes_errados: list[int]) -> pd.DataFrame:
    passes = []
    for i in range(0, len(coords), 2):
        start = coords[i]
        end = coords[i + 1]
        numero = i // 2 + 1  # 1-indexed within the match
        passes.append(
            {
                "numero": numero,
                "x_start": float(start[0]),
                "y_start": float(start[1]),
                "x_end": float(end[0]),
                "y_end": float(end[1]),
            }
        )

    df = pd.DataFrame(passes)
    df["errado"] = df["numero"].isin(passes_errados)
    df["certo"] = ~df["errado"]

    # Passes in final third: x_end >= 80
    df["in_final_third"] = df["x_end"] >= FINAL_THIRD_LINE_X

    # Passes to the box: x_end >= 100
    df["to_box"] = df["x_end"] >= 100
    return df


def compute_stats(df: pd.DataFrame) -> dict:
    total_passes = len(df)
    successful = int(df["certo"].sum())
    unsuccessful = int(df["errado"].sum())

    accuracy = (successful / total_passes * 100.0) if total_passes else 0.0

    final_third_total = int(df["in_final_third"].sum())
    final_third_success = int((df["in_final_third"] & ~df["errado"]).sum())
    final_third_unsuccess = int((df["in_final_third"] & df["errado"]).sum())
    final_third_accuracy = (
        final_third_success / final_third_total * 100.0 if final_third_total else 0.0
    )

    box_total = int(df["to_box"].sum())
    box_success = int((df["to_box"] & ~df["errado"]).sum())
    box_unsuccess = int((df["to_box"] & df["errado"]).sum())
    box_accuracy = (
        box_success / box_total * 100.0 if box_total else 0.0
    )

    return {
        "total_passes": total_passes,
        "successful_passes": successful,
        "unsuccessful_passes": unsuccessful,
        "accuracy_pct": round(accuracy, 2),
        "final_third_total": final_third_total,
        "final_third_success": final_third_success,
        "final_third_unsuccess": final_third_unsuccess,
        "final_third_accuracy_pct": round(final_third_accuracy, 2),
        "box_total": box_total,
        "box_success": box_success,
        "box_unsuccess": box_unsuccess,
        "box_accuracy_pct": round(box_accuracy, 2),
    }


def draw_pass_map(df: pd.DataFrame):
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#f5f5f5", line_color="#4a4a4a")

    # Smaller map + similar resolution
    fig, ax = pitch.draw(figsize=(6.4, 4.2))
    fig.set_dpi(100)

    ax.axvline(x=FINAL_THIRD_LINE_X, color="#FFD54F", linewidth=1.2, alpha=0.25)

    # Colors
    for _, row in df.iterrows():
        if row["errado"]:
            # red for unsuccessful
            color = (0.95, 0.18, 0.18, 0.65)
            width = 1.55
            headwidth = 2.25
            headlength = 2.25
        else:
            # green for successful
            color = (0.18, 0.8, 0.18, 0.65)
            width = 1.55
            headwidth = 2.25
            headlength = 2.25

        pitch.arrows(
            row["x_start"],
            row["y_start"],
            row["x_end"],
            row["y_end"],
            color=color,
            width=width,
            headwidth=headwidth,
            headlength=headlength,
            ax=ax,
        )

    ax.set_title(f"Pass Map - {selected_match}", fontsize=12)

    # Elegant smaller legend top-left
    legend_elements = [
        Line2D(
            [0],
            [0],
            color=(0.18, 0.8, 0.18, 0.65),
            lw=2.5,
            label="Successful Pass",
        ),
        Line2D(
            [0],
            [0],
            color=(0.95, 0.18, 0.18, 0.65),
            lw=2.5,
            label="Unsuccessful Pass",
        ),
    ]
    legend = ax.legend(
        handles=legend_elements,
        loc="upper left",
        bbox_to_anchor=(0.01, 0.99),
        frameon=True,
        facecolor="white",
        edgecolor="#cccccc",
        shadow=False,
        fontsize="x-small",
        labelspacing=0.5,
        borderpad=0.5,
    )
    legend.get_frame().set_alpha(1.0)

    # Attack direction arrow: middle-bottom
    arrow = FancyArrowPatch(
        (0.45, 0.05),
        (0.55, 0.05),
        transform=fig.transFigure,
        arrowstyle="-|>",
        mutation_scale=15,
        linewidth=2,
        color="#333333",
    )
    fig.patches.append(arrow)
    fig.text(
        0.5,
        0.02,
        "Attack Direction",
        ha="center",
        va="center",
        fontsize=9,
        color="#333333",
    )

    fig.tight_layout()

    # Render controlled to avoid oversized display
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    buf.seek(0)
    img = Image.open(buf)
    plt.close(fig)
    return img


if selected_match == "All Matches":
    all_coords = []
    all_errados = []
    offset = 0
    for match in MATCHES[:-1]:  # exclude "All Matches"
        coords_match = coords_by_match[match]
        errados_match = passes_errados_by_match[match]
        all_coords.extend(coords_match)
        all_errados.extend([e + offset for e in errados_match])
        offset += len(coords_match) // 2
    coords = all_coords
    errados = all_errados
else:
    coords = coords_by_match[selected_match]
    errados = passes_errados_by_match[selected_match]

df = build_df(coords, errados)

# Apply pass filter
if pass_filter == "Successful Only":
    df = df[df["certo"]].reset_index(drop=True)
elif pass_filter == "Unsuccessful Only":
    df = df[df["errado"]].reset_index(drop=True)

stats = compute_stats(df)

# ==========================
# Dashboard layout
# ==========================
col_stats, col_map = st.columns([1, 2], gap="large")

with col_stats:
    st.subheader("Statistics")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Passes", stats["total_passes"])
    c2.metric("Successful", stats["successful_passes"])
    c3.metric("Accuracy", f'{stats["accuracy_pct"]:.1f}%')
    c4.metric("Unsuccessful", stats["unsuccessful_passes"])

    st.divider()

    st.subheader("Final Third")
    c7, c8, c9 = st.columns(3)
    c7.metric("Total", stats["final_third_total"])
    c8.metric("Successful", stats["final_third_success"])
    c9.metric("Unsuccessful", stats["final_third_unsuccess"])
    st.metric("Accuracy", f'{stats["final_third_accuracy_pct"]:.1f}%')

    st.divider()

    st.subheader("Passes to the Box")
    d1, d2, d3 = st.columns(3)
    d1.metric("Total", stats["box_total"])
    d2.metric("Successful", stats["box_success"])
    d3.metric("Unsuccessful", stats["box_unsuccess"])
    st.metric("Accuracy", f'{stats["box_accuracy_pct"]:.1f}%')

with col_map:
    st.subheader("Pass Map")
    img = draw_pass_map(df)
    st.image(img, width=620)
