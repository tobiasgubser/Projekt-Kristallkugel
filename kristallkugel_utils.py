import pandas                 as pd
import numpy                  as np
import matplotlib.pyplot      as plt
import seaborn                as sns
import plotly.express         as px
import matplotlib.ticker      as mtick
import matplotlib.dates       as mdates
import ipywidgets             as widgets
from IPython.display import display, HTML, Javascript
import io
import requests
import re
from datetime import date
import os
from statsmodels.nonparametric.smoothers_lowess import lowess
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import skew, kurtosis # Rendite & Verteilung

# ---------------------------------------------------------------------
# Funktionen für "Projekt Kristallkugel.ipynb"
# ---------------------------------------------------------------------
# ------------------------------------
# Funktion für Übersichtstabellen
# ------------------------------------
def overview_table(df):
    numeric_cols = df.select_dtypes(include="number").columns

    # Basis-Infos
    info_table = (
        df.dtypes.to_frame("Dtype")
        .join(df.notna().sum().to_frame("Non-Null"))
    )
    missing_table = df.isna().sum().rename("Missing")

    # describe(include="all") für ALLE Spalten
    describe_table = (
        df.describe(include="all")
        .T
        .drop(columns=["count"], errors="ignore")
    )

    # Varianz nur für numerische Spalten
    variance_table = df[numeric_cols].var().rename("Varianz")

    # Zusammenführen
    overview = (
        info_table
        .join(missing_table)
        .join(describe_table, how="left")
        .join(variance_table, how="left")
    )

    # Spalten sauber umbenennen
    overview = overview.rename(columns={
        "mean": "Mittelwert",
        "std": "Standardabweichung",
        "min": "Minimum",
        "25%": "Q1 (25%)",
        "50%": "Median",
        "75%": "Q3 (75%)",
        "max": "Maximum",
    })

    # Zielspalten
    desired_cols = [
        "Dtype", "Non-Null", "Missing",
        "Median", "Mittelwert", "Q1 (25%)", "Q3 (75%)",
        "Standardabweichung", "Varianz", "Minimum", "Maximum"
    ]

    # Nur existierende Spalten auswählen → verhindert jeden KeyError
    existing_cols = [c for c in desired_cols if c in overview.columns]

    return overview[existing_cols]

def show_df_overview(df):
    display(style_table(overview_table(df)))
    print()
    print("Beispiele aus dem Dataframe")
    display(style_table(df.head()))

# ------------------------------------
#  Funktion für Tabellen-Layout
# ------------------------------------
def style_table(df):
    def fmt(x):
        if isinstance(x, bool):
            return "True" if x else "False"
        if isinstance(x, int) and not isinstance(x, bool):
            return f"{x:,}".replace(",", "'")
        if isinstance(x, float) and pd.notnull(x):
            return f"{x:,.2f}".replace(",", "'")
        return x

    table_styles = [
        {"selector": "table", "props": [("border-collapse", "collapse")]},
        {"selector": "th", "props": [("border", "1px solid #bfbfbf"), ("padding", "6px")]},
        {"selector": "td", "props": [("border", "1px solid #bfbfbf"), ("padding", "6px")]},
        {"selector": "th.col_heading.level0", "props": [("background-color", "#dedede")]},
    ]
    return (df.style.format(fmt).set_table_styles(table_styles))

# ------------------------------------
#  Funktion für Shift auf nächsten Handelstag
# ------------------------------------

def shift_to_next_trading_day(df_source, df_spi):
    # Sicherstellen, dass Index sortiert ist
    df_source = df_source.sort_index()

    # Mapping: jeder Source-Tag → nächster Handelstag
    next_idx_pos = df_spi.index.searchsorted(df_source.index)
    next_idx_pos = next_idx_pos.clip(0, len(df_spi.index) - 1)
    mapped_days = df_spi.index[next_idx_pos]
    df_source["next_trading_day"] = mapped_days
    df_source = df_source.groupby("next_trading_day").last()

    # Reindex auf Trading-Index
    df_source = df_source.reindex(df_spi.index)
    df_source = df_source.drop(columns=["next_trading_day"], errors="ignore")

    return df_source

# ------------------------------------
#  Funktion für Plots
# ------------------------------------
def describing_plots(df_all, cols):

    # ------------------------------------
    #  Tabelle für ALLE Variablen
    # ------------------------------------
    merged = overview_table(df_all)
    stats_df = merged.loc[cols]
    display(style_table(stats_df))

    # ------------------------------------
    #  Für jede Variable: Boxplot + Lineplot
    # ------------------------------------
    for col in cols:

        data = df_all[col].dropna()
        stats = stats_df.loc[col]

        # Figure
        fig, axes = plt.subplots(
            1, 2, figsize=(20, 5),
            gridspec_kw={'width_ratios': [1, 5]}
        )
        sns.set_theme(style="white")
        ax0, ax1 = axes

        # Gemeinsamer Titel
        clean_col = re.sub(r"^[A-Za-z0-9_]+?_", "", col)
        fig.suptitle(clean_col, fontsize=14, fontweight="bold", y=1.03)

        # ------------------------------------
        #  BOX PLOT
        # ------------------------------------
        sns.boxplot(
            data=data,
            color='#E0E0E0',
            width=0.5,
            ax=ax0,
            boxprops={'edgecolor': 'black', 'linewidth': 1.5},
            medianprops={'color': 'black', 'linewidth': 2},
            whiskerprops={'color': 'black', 'linewidth': 1.5},
            capprops={'color': 'black', 'linewidth': 1.5},
            flierprops={'marker': 'o', 'markerfacecolor': 'black',
                        'markeredgecolor': 'black', 'markersize': 4}
        )

        sns.despine(ax=ax0, left=True, bottom=True, top=True, right=True)
        ax0.set_xticks([]); ax0.set_yticks([]); ax0.set_xlabel(''); ax0.set_ylabel('')

        # Boxplot-Beschriftungen
        x_left = 0.20
        x_right = 0.35

        def label(x, y, text):
            ax0.annotate(
                f"{text:.2f}",
                xy=(x, y),
                xytext=(x, 0),
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=9,
                color="black"
            )

        label(x_left,  stats["Minimum"],    stats["Minimum"])
        label(x_right, stats["Q1 (25%)"],   stats["Q1 (25%)"])
        label(x_right, stats["Median"],     stats["Median"])
        label(x_right, stats["Q3 (75%)"],   stats["Q3 (75%)"])
        label(x_left,  stats["Maximum"],    stats["Maximum"])

        # ------------------------------------
        #  LINE PLOT (Tagesdaten)
        # ------------------------------------
        sns.lineplot(
            data=df_all,
            x=df_all.index,
            y=col,
            color='black',
            linewidth=2,
            ax=ax1
        )

        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

        sns.despine(ax=ax1, left=True, bottom=True, top=True, right=True)
        ax1.set_xlabel('')
        ax1.tick_params(axis='x', length=4, color='black', labelsize=8)
        ax1.set_yticks([]); ax1.set_ylabel('')
        ax1.axhline(0, color='black', linewidth=1)

        # Annotationen
        daily = df_all[col]
        targets = {
            "Minimum": daily.min(),
            "Maximum": daily.max(),
            "Median": daily.median(),
            "Mittelwert": daily.mean(),
            "Q1 (25%)": daily.quantile(0.25),
            "Q3 (75%)": daily.quantile(0.75)
        }

        for val in targets.values():
            idx = (daily - val).abs().idxmin()
            ax1.annotate(
                f"{daily.loc[idx]:.2f}",
                xy=(idx, daily.loc[idx]),
                xytext=(0, 12),
                textcoords='offset points',
                ha='center',
                va='bottom',
                fontsize=9,
                color='black',
                bbox=dict(
                    facecolor='white',
                    edgecolor='none',
                    boxstyle='round,pad=0.2',
                    alpha=0.9
                )
            )

        plt.tight_layout(w_pad=4.0)
        plt.show()

  # ------------------------------------
# Funktion für Heatmap & Scatterplots
# ------------------------------------
def heatmaps_scatterplots(df_all, cols, title):
    def strip_prefix(colname):
        return colname.split("_", 1)[-1]

    # --- Spearman-Korrelation berechnen ---
    corr_spearman = (df_all[cols]
        .corrwith(df_all["SPI (%)"], method="spearman")
        .to_frame()
        .T
    )
    corr_spearman.index = ["SPI (%)"]
    corr_spearman.columns = [strip_prefix(c) for c in corr_spearman.columns]

    plt.figure(figsize=(20, 2))
    sns.heatmap(
        corr_spearman,
        annot=True,
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        fmt=".2f",
        linewidths=0.5
    )
    plt.title(f"Spearman-Korrelation: SPI-Rendite vs. {title}")
    plt.yticks(rotation=0)
    plt.show()

    # --- Scatterplots ---
    n_vars = len(cols)
    n_cols = 3
    n_rows = (n_vars + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
    axes = axes.flatten()

    for ax, var in zip(axes, cols):
        sns.regplot(
            data=df_all,
            x=var,
            y="SPI (%)",
            ax=ax,
            scatter_kws={"alpha": 0.4},
            line_kws={"color": "red"}
        )
        ax.set_title(f"SPI-Rendite vs. {strip_prefix(var)}")

    # --- Leere Achsen ausblenden ---
    for ax in axes[n_vars:]:
        ax.set_visible(False)

    plt.tight_layout()
    plt.show()

# ------------------------------------
# Funktion für Rolling-Analysen
# ------------------------------------
def rolling_analysis(series, window=30):

    # NaN-Werte ersetzen
    series = series.fillna(0)

    # Rolling Mean und Rolling Std für 30 Tage-Fenster berechnen
    rolling_mean = series.rolling(window=window).mean()
    rolling_std  = series.rolling(window=window).std()

    # Plot erstellen
    plt.figure(figsize=(12, 5))
    plt.plot(rolling_mean, label=f"Rolling Mean ({window} Tage)", color="darkgreen")
    plt.plot(rolling_std,  label=f"Rolling Std ({window} Tage)",  color="darkred")
    plt.title("Rolling-Analyse")
    plt.xlabel("Datum")
    plt.ylabel("Wert")
    plt.legend()
    plt.show()

# ------------------------------------
# Funktion für Rolling-Korrelationen
# ------------------------------------
def rolling_correlation(series_x, series_y, window=30):

    # NaN-Werte ersetzen
    series_x = series_x.fillna(0)
    series_y = series_y.fillna(0)

    # Rolling-Korrelation direkt berechnen
    rolling_corr = series_x.rolling(window).corr(series_y)

    # Plot
    plt.figure(figsize=(12, 5))
    plt.plot(rolling_corr, color="darkblue", label=f"Rolling-Korrelation ({window} Tage)")
    plt.axhline(0, color="black", linewidth=1)
    plt.title("Rolling-Korrelation")
    plt.xlabel("Datum")
    plt.ylabel("Korrelation")
    plt.legend()
    plt.show()

# ------------------------------------
# Kompakte & reduzierte Rolling-Korrelationen im Grid
# ------------------------------------
def rolling_correlation_multi(df_all, cols, title, window=30):

    def strip_prefix(colname):
        return colname.split("_", 1)[-1]

    series_x = df_all["SPI (%)"]
    n_vars = len(cols)

    # Grid definieren (3 Spalten wie bei Spearman)
    n_cols = 3
    n_rows = (n_vars + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 3.2 * n_rows))
    axes = axes.flatten()

    for ax, col in zip(axes, cols):
        series_y = df_all[col].fillna(0)
        rolling_corr = series_x.rolling(window).corr(series_y)

        # Linie
        ax.plot(rolling_corr, color="darkblue", linewidth=1)

        # Null-Linie
        ax.axhline(0, color="black", linewidth=0.8)

        # Titel kompakt
        ax.set_title(strip_prefix(col), fontsize=10)

        # Achsen minimalistisch
        ax.tick_params(axis="both", labelsize=8)
        ax.set_xlabel("")
        ax.set_ylabel("")

        # Weniger Ticks
        ax.xaxis.set_major_locator(plt.MaxNLocator(3))
        ax.yaxis.set_major_locator(plt.MaxNLocator(3))

    # Leere Achsen ausblenden
    for ax in axes[n_vars:]:
        ax.set_visible(False)

    plt.suptitle(f"Rolling-Korrelation: SPI-Rendite vs. {title} ({window} -Tage‑Fenster)", fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()

# ---------------------------------------------------------
# Lag-Korrelationsmatrix berechnen (mit SPI-Rendite)
# ---------------------------------------------------------
def lag_analysis(df_all, cols, title):
  lags = range(0, 8)
  corr_matrix = pd.DataFrame(index=cols, columns=range(0, 8))

  for var in cols:
      for lag in lags:
          corr_matrix.loc[var, lag] = df_all["SPI (%)"].corr(
              df_all[var].shift(lag), method="pearson"
          )

  corr_matrix = corr_matrix.astype(float)

  # --- Heatmap plotten ---
  plt.figure(figsize=(20, 6))
  sns.heatmap(
      corr_matrix,
      annot=True,
      cmap="coolwarm",
      vmin=-1,
      vmax=1,
      fmt=".2f",
      linewidths=0.5
  )

  plt.title(f"Lag-Analyse (0–7 Tage): SPI-Rendite vs. {title}")
  plt.xlabel("Lag (Tage)")
  plt.ylabel(f'{title}')
  plt.tight_layout()
  plt.show()
