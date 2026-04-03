import streamlit as st
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import pandas as pd
import numpy as np
from PIL import Image
from io import BytesIO
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from streamlit_image_coordinates import streamlit_image_coordinates

# ==========================
# Page Configuration
# ==========================
st.set_page_config(layout="wide", page_title="Pass Map Dashboard (Interactive)")
st.title("Pass Map Dashboard")
st.caption("Clique na bolinha no início do passe para ver o vídeo (se houver).")

# ==========================
# Configuration
# ==========================
FINAL_THIRD_LINE_X = 80

# ==========================
# DATA (respeitando exatamente o que você passou)
# type, x_start, y_start, x_end, y_end, video
# ==========================
matches_data = {
    "Vs Los Angeles": [
        ("PASS WON", 52.52, 13.90, 78.12, 72.42, None),
        ("PASS WON", 98.73, 43.66, 90.42, 36.84, "videos/Sebas - KP Los Angeles.mp4"),
        ("PASS WON", 105.55, 22.38, 99.23, 48.98, None),

        ("PASS LOST", 72.63, 9.41, 93.08, 18.06, None),
        ("PASS LOST", 105.38, 18.06, 108.37, 30.69, None),
        ("PASS LOST", 105.05, 48.15, 100.89, 40.33, None),
        ("PASS LOST", 99.06, 56.96, 116.52, 65.43, None),
        ("PASS LOST", 42.21, 41.99, 49.19, 54.13, None),
    ],
    "Vs Slavia Praha": [
        ("PASS WON", 91.25, 28.53, 100.73, 19.39, "videos/Sebas - KP Slavia.mp4"),
        ("PASS WON", 95.91, 27.03, 104.72, 16.89, None),
        ("PASS WON", 103.55, 21.05, 101.23, 45.98, None),
        ("PASS WON", 85.60, 53.63, 91.42, 59.12, None),

        ("PASS LOST", 119.68, 21.55, 111.86, 37.84, None),
        ("PASS LOST", 94.58, 27.03, 101.39, 22.88, None),
        ("PASS LOST", 117.52, 67.59, 105.22, 25.37, None),
    ],
    "Vs Sockers": [
        ("PASS WON", 114.36, 66.93, 104.38, 42.83, None),
        ("PASS WON", 70.97, 30.19, 77.79, 41.33, None),
        ("PASS WON", 64.49, 35.35, 71.47, 52.63, None),
        ("PASS WON", 51.52, 26.87, 65.15, 21.05, None),

        ("PASS LOST", 110.37, 13.90, 114.03, 46.32, None),
        ("PASS LOST", 93.25, 73.08, 109.21, 42.83, "videos/Sebas - KP Sockers.mp4"),
        ("PASS LOST", 79.28, 3.59, 95.24, 36.51, None),
    ],
}

# Create DataFrames for each match and combined
dfs_by_match = {}
for match_name, events in matches_data.items():
    dfm = pd.DataFrame(events, columns=["type", "x_start", "y_start", "x_end", "y_end", "video"])
    dfm["numero"] = np.arange(1, len(dfm) + 1)
    dfs_by_match[match_name] = dfm

df_all = pd.concat(dfs_by_match.values(), ignore_index=True)
full_data = {"All Matches": df_all}
full_data.update(dfs_by_match)

# ==========================
# Stats
# ==========================
def compute_stats(df: pd.DataFrame) -> dict:
    total_passes = len(df)
    successful = int(df["type"].str.contains("WON", case=False).sum())
    unsuccessful = int(df["type"].str.contains("LOST", case=False).sum())
    accuracy = (successful / total_passes * 100.0) if total_passes else 0.0

    in_final_third = df["x_end"] >= FINAL_THIRD_LINE_X
    final_third_total = int(in_final_third.sum())
    final_third_success = int((in_final_third & df["type"].str.contains("WON", case=False)).sum())
    final_third_unsuccess = int((in_final_third & df["type"].str.contains("LOST", case=False)).sum())
    final_third_accuracy = (final_third_success / final_third_total * 100.0) if final_third_total else 0.0

    to_box = df["x_end"] >= 100
    box_total = int(to_box.sum())
    box_success = int((to_box & df["type"].str.contains("WON", case=False)).sum())
    box_unsuccess = int((to_box & df["type"].str.contains("LOST", case=False)).sum())
    box_accuracy = (box_success / box_total * 100.0) if box_total else 0.0

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

# ==========================
# Draw
# ==========================
def draw_pass_map(df: pd.DataFrame, title: str):
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#f5f5f5", line_color="#4a4a4a")
    fig, ax = pitch.draw(figsize=(7.9, 5.3))  # um pouco aumentado
    fig.set_dpi(110)

    ax.axvline(x=FINAL_THIRD_LINE_X, color="#FFD54F", linewidth=1.2, alpha=0.25)

    # tamanho menor da bolinha
    START_DOT_SIZE = 55

    for _, row in df.iterrows():
        is_lost = "LOST" in row["type"].upper()

        if is_lost:
            color = (0.95, 0.18, 0.18, 0.65)
        else:
            color = (0.18, 0.8, 0.18, 0.65)

        pitch.arrows(
            row["x_start"], row["y_start"],
            row["x_end"], row["y_end"],
            color=color,
            width=1.55,
            headwidth=2.25,
            headlength=2.25,
            ax=ax,
            zorder=3,
        )

        # bolinha no início (sem borda preta)
        pitch.scatter(
            row["x_start"], row["y_start"],
            s=START_DOT_SIZE,
            marker="o",
            color=color,
            edgecolors="white",
            linewidths=1.0,
            ax=ax,
            zorder=4,
        )

    ax.set_title(title, fontsize=12)

    legend_elements = [
        Line2D([0], [0], color=(0.18, 0.8, 0.18, 0.65), lw=2.5, label="Successful Pass"),
        Line2D([0], [0], color=(0.95, 0.18, 0.18, 0.65), lw=2.5, label="Unsuccessful Pass"),
        Line2D([0], [0], marker="o", color="w",
               markerfacecolor=(0.6, 0.6, 0.6, 0.65), markeredgecolor="white",
               markersize=6, label="Start point (click)"),
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
    fig.text(0.5, 0.02, "Attack Direction", ha="center", va="center", fontsize=9, color="#333333")

    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    buf.seek(0)
    img_obj = Image.open(buf)
    return img_obj, ax, fig

# ==========================
# Sidebar
# ==========================
st.sidebar.header("Match selection")
selected_match = st.sidebar.radio("Choose the match", list(full_data.keys()), index=0)

st.sidebar.header("Pass filter")
pass_filter = st.sidebar.radio(
    "Filter passes",
    ["All Passes", "Successful Only", "Unsuccessful Only"],
    index=0
)

df = full_data[selected_match].copy()

if pass_filter == "Successful Only":
    df = df[df["type"].str.contains("WON", case=False)].reset_index(drop=True)
elif pass_filter == "Unsuccessful Only":
    df = df[df["type"].str.contains("LOST", case=False)].reset_index(drop=True)

stats = compute_stats(df)

# ==========================
# Layout
# ==========================
col_stats, col_right = st.columns([1, 2], gap="large")

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

with col_right:
    st.subheader("Pass Map (click the start dot)")

    img_obj, ax, fig = draw_pass_map(df, title=f"Pass Map - {selected_match}")

    # um pouco maior na tela
    click = streamlit_image_coordinates(img_obj, width=780)

    selected_pass = None
    if click is not None:
        # --- clique em pixels reais da imagem ---
        real_w, real_h = img_obj.size
        disp_w, disp_h = click["width"], click["height"]

        pixel_x = click["x"] * (real_w / disp_w)
        pixel_y = click["y"] * (real_h / disp_h)

        # eixo do matplotlib tem origem embaixo
        mpl_pixel_y = real_h - pixel_y

        # --- Melhor seleção: comparar em PIXELS ---
        # transforma o (x_start, y_start) de cada passe para pixel do PNG
        df_sel = df.copy()
        start_pixels = df_sel.apply(
            lambda r: ax.transData.transform((r["x_start"], r["y_start"])),
            axis=1
        )
        df_sel["sx_px"] = [p[0] for p in start_pixels]
        df_sel["sy_px"] = [p[1] for p in start_pixels]

        df_sel["dist_px"] = np.sqrt((df_sel["sx_px"] - pixel_x) ** 2 + (df_sel["sy_px"] - mpl_pixel_y) ** 2)

        RADIUS_PX = 18  # ajuste fino (em pixels) - normalmente bem melhor que "unidades do campo"
        candidates = df_sel[df_sel["dist_px"] < RADIUS_PX]
        if not candidates.empty:
            selected_pass = candidates.loc[candidates["dist_px"].idxmin()]

    plt.close(fig)

    st.divider()
    st.subheader("Video")

    if selected_pass is None:
        st.info("Clique na bolinha no início do passe para ver o vídeo (se houver).")
    else:
        st.success(f"Selected pass: #{int(selected_pass['numero'])} ({selected_pass['type']})")
        st.write(
            f"Start: ({selected_pass['x_start']:.2f}, {selected_pass['y_start']:.2f})  \n"
            f"End: ({selected_pass['x_end']:.2f}, {selected_pass['y_end']:.2f})"
        )

        if selected_pass["video"]:
            try:
                st.video(selected_pass["video"])
            except Exception:
                st.error(f"Video file not found: {selected_pass['video']}")
        else:
            st.warning("Não há vídeo carregado para este evento.")
