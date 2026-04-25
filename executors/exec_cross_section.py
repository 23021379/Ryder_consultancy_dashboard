import matplotlib.pyplot as plt
import numpy as np

def generate_single_cross_section(width, gap, s_pitch, n_pitch, p_change, title_str="Optimal Configuration"):
    fixed_roof_span_m = 250.0
    num_panels = int((fixed_roof_span_m + gap) // (width + gap))
    max_start_x = (num_panels - 1) * (width + gap)

    fig, ax = plt.subplots(figsize=(16, 3.5))
    ax.set_title(title_str, fontsize=14, fontweight='bold', loc='left')
    ax.plot([0, max_start_x + width], [0, 0], color='black', linewidth=2)

    current_x = 0
    panel_count = 0

    while current_x <= max_start_x + 0.1:
        # figure out how far along the roof we are, from 0.0 (south) to 1.0 (north)
        pos_norm = current_x / max_start_x if max_start_x > 0 else 0
        pos_norm = min(pos_norm, 1.0)

        # bend the pitch based on the exponent (pitch_change) so the slope gets steeper/shallower as we move north
        pitch = s_pitch + (n_pitch - s_pitch) * (pos_norm ** p_change)
        pitch_rad = np.radians(pitch)
        peak_z = width * np.tan(pitch_rad)

        # draw the literal triangle for the panel and its support strut
        ax.plot([current_x, current_x + width], [0, peak_z], color='#1f77b4', linewidth=3)
        ax.plot([current_x + width, current_x + width], [peak_z, 0], color='gray', linestyle='--', linewidth=1)
        ax.text(current_x + (width/2), peak_z/2 + 0.5, f"{pitch:.1f}°", 
                fontsize=9, color='darkblue', rotation=pitch, ha='center', va='bottom')

        # scribble some little arrows on the very first panel so people know what width and gap mean
        if panel_count == 0:
            ax.annotate('', xy=(current_x, -1), xytext=(current_x + width, -1), arrowprops=dict(arrowstyle='<->', color='green'))
            ax.text(current_x + width/2, -2.5, f"W: {width}m", ha='center', color='green', fontsize=9)
            ax.annotate('', xy=(current_x + width, -1), xytext=(current_x + width + gap, -1), arrowprops=dict(arrowstyle='<->', color='red'))
            ax.text(current_x + width + gap/2, -2.5, f"G: {gap}m", ha='center', color='red', fontsize=9)

        current_x += (width + gap)
        panel_count += 1

    # Axis bounds
    ax.set_xlabel("Distance from Southern Edge (South -> North in meters)", fontsize=11)
    ax.set_ylabel("Elevation (m)")
    
    # lock the axes and grid so it looks like a clean blueprint
    max_pitch = max(s_pitch, n_pitch)
    y_upper = width * np.tan(np.radians(max_pitch)) + 2
    ax.set_ylim(-3, y_upper)
    ax.grid(True, linestyle=':', alpha=0.6)

    fig.tight_layout()
    return fig
