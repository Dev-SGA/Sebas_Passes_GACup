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
st.caption("Clique em uma seta no campo para ver o vídeo do passe (se houver).")

# ==========================
# Configuration
# ==========================
FINAL_THIRD_LINE_X = 80
MATCHES = ["Vs Los Angeles", "Vs Slavia Praha", "Vs Sockers", "All Matches"]

# ==========================
# DATA (AGORA NO MESMO PADRÃO DOS OUTROS CÓDIGOS)
# type, x_start, y_start, x_end, y_end, video
# - Use "PASS WON" = passe certo
# - Use "PASS LOST" = passe errado
# - No campo video, coloque None ou o link/path do vídeo
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

        # Exemplo com vídeo:
        # ("PASS WON", 60.00, 20.00, 88.00, 30.00, "videos/la_pass_09.mp4"),
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
    dfs_by_match[match_name] = pd.DataFrame(
        events,
        columns=["type", "x_start", "y_start", "x_end", "y_end", "video"]
    )
    dfs_by_match[match_name]["numero"] = np.arange(1, len(dfs_by_match[match_name]) + 1)

df_all = pd.concat(dfs_by_match.values(), ignore_index=True)
full_data = {"All Matches": df_all}
full_data.update(dfs_by_match)

def compute_stats(df: pd.DataFrame) -> dict:
    total_passes = len(df)
    successful = int((df["type"].str.contains("WON", case=False)).sum())
    unsuccessful = int((df["type"].str.contains("LOST", case=False)).sum())
    accuracy = (successful / total_passes * 100.0) if total_passes else 0.0

    in_final_third = df["x_end"] >= FINAL_THIRD_LINE_X
    final_third_total = int(in_final_third.sum())
    final_third_success = int((in_final_third & df["type"].str.contains("WON", case=False)).sum())
    final_third_unsuccess = int((in_final_third & df["type"].str.contains("LOST", case=False)).sum())
    final_third_accuracy = final_third_success / final_third_total * 100.0 if final_third_total else 0.0

    to_box = df["x_end"] >= 100
    box_total = int(to_box.sum())
    box_success = int((to_box & df["type"].str.contains("WON", case=False)).sum())
    box_unsuccess = int((to_box & df["type"].str.contains("LOST", case=False)).sum())
    box_accuracy = box_success / box_total * 100.0 if box_total else 0.0

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

def draw_pass_map(df: pd.DataFrame, title: str):
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#f5f5f5", line_color="#4a4a4a")
    fig, ax = pitch.draw(figsize=(7.6, 5.1))
    fig.set_dpi(100)

    ax.axvline(x=FINAL_THIRD_LINE_X, color="#FFD54F", linewidth=1.2, alpha=0.25)

    for _, row in df.iterrows():
        is_lost = "LOST" in row["type"].upper()
        has_vid = row["video"] is not None

        if is_lost:
            color = (0.95, 0.18, 0.18, 0.65)
        else:
            color = (0.18, 0.8, 0.18, 0.65)

        width = 1.55
        headwidth = 2.25
        headlength = 2.25

        # Borda preta se tem vídeo
        if has_vid:
            pitch.arrows(
                row["x_start"], row["y_start"],
                row["x_end"], row["y_end"],
                color=(0, 0, 0, 0.95),
                width=width + 0.9,
                headwidth=headwidth + 1.2,
                headlength=headlength + 1.2,
                ax=ax,
                zorder=2
            )

        pitch.arrows(
            row["x_start"], row["y_start"],
            row["x_end"], row["y_end"],
            color=color,
            width=width,
            headwidth=headwidth,
            headlength=headlength,
            ax=ax,
            zorder=3
        )

    ax.set_title(title, fontsize=12)

    legend_elements = [
        Line2D([0], [0], color=(0.18, 0.8, 0.18, 0.65), lw=2.5, label="Successful Pass"),
        Line2D([0], [0], color=(0.95, 0.18, 0.18, 0.65), lw=2.5, label="Unsuccessful Pass"),
        Line2D([0], [0], color="black", lw=2.5, label="Has video (black border)"),
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
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
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
    st.subheader("Pass Map (click an arrow)")

    img_obj, ax, fig = draw_pass_map(df, title=f"Pass Map - {selected_match}")
    click = streamlit_image_coordinates(img_obj, width=740)

    selected_pass = None
    if click is not None:
        real_w, real_h = img_obj.size
        disp_w, disp_h = click["width"], click["height"]

        pixel_x = click["x"] * (real_w / disp_w)
        pixel_y = click["y"] * (real_h / disp_h)

        mpl_pixel_y = real_h - pixel_y
        field_x, field_y = ax.transData.inverted().transform((pixel_x, mpl_pixel_y))

        # Seleção pelo meio da seta (robusto)
        df_sel = df.copy()
        df_sel["x_mid"] = (df_sel["x_start"] + df_sel["x_end"]) / 2.0
        df_sel["y_mid"] = (df_sel["y_start"] + df_sel["y_end"]) / 2.0
        df_sel["dist"] = np.sqrt((df_sel["x_mid"] - field_x) ** 2 + (df_sel["y_mid"] - field_y) ** 2)

        RADIUS = 6
        candidates = df_sel[df_sel["dist"] < RADIUS]
        if not candidates.empty:
            selected_pass = candidates.loc[candidates["dist"].idxmin()]

    plt.close(fig)

    st.divider()
    st.subheader("Video")

    if selected_pass is None:
        st.info("Clique em uma seta para ver o vídeo do passe (se houver).")
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
