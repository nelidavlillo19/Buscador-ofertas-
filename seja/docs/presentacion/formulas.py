"""Dibuja las fórmulas de la presentación como PNG transparentes (mathtext de matplotlib)."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

matplotlib.rcParams["mathtext.fontset"] = "cm"

FORMULAS = {
    "pauta": r"$p_t = \dfrac{C}{C + NC} \times 100$",
    "escala": r"$p_t = \dfrac{x - x_{\min}}{x_{\max} - x_{\min}} \times 100$",
    "meta": r"$p_t = \min\left(\dfrac{L}{M \cdot f},\ 1\right) \times 100$",
    "excedente": r"$p_t = \min\left(\dfrac{L}{M \cdot f} \times 100,\ 120\right)$",
    "ambito": r"$S_a = \dfrac{\sum_{t \in a} \pi_t \, p_t}{\sum_{t \in a} \pi_t}$",
    "horas": r"$h_a = \dfrac{1}{|S|}\sum_{s \in S} h_{a,s}$",
    "peso": r"$w_a = \dfrac{h_a}{\sum_b h_b}$",
    "compromiso": r"$C = \sum_a w_a \, S_a$",
    "final": r"$F = (1 - 2p) \cdot C \;+\; p \cdot AE \;+\; p \cdot EE$",
    "factor": r"$f = \dfrac{\%\ \mathrm{jornada\ dedicada}}{100}$",
}


def dibujar(salida: Path, color: str = "#1B2A49") -> None:
    salida.mkdir(parents=True, exist_ok=True)
    for nombre, tex in FORMULAS.items():
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, tex, fontsize=34, color=color)
        fig.savefig(salida / f"{nombre}.png", dpi=220, transparent=True, bbox_inches="tight", pad_inches=0.04)
        plt.close(fig)


if __name__ == "__main__":
    dibujar(Path(sys.argv[1]))
