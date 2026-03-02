import pandas as pd
import glob
from pathlib import Path

#https://gme.mercatoelettrico.org/it-it/Home/Esiti/Elettricita/MGP/Statistiche/DatiStorici#IntestazioneGrafico
DATA_DIR = Path("pun_data")
#files = sorted(DATA_DIR.glob("PUN_*.csv"))
year=2009
file=f"{DATA_DIR}/PUN_{year}.csv"
df = pd.read_csv(file)

    # Build timestamp from DAY + HOUR
dt = (
        pd.to_datetime(df["DAY"].astype(str), format="%Y%m%d")
        + pd.to_timedelta(df["HOUR"] - 1, unit="h")  # remove -1 if HOUR is 0–23
    )
df_clean = pd.DataFrame({
        "datetime": dt,
        "pun": df["PUN INDEX GME"]
    }).sort_values("datetime")

#output_name = file.with_suffix(".parquet")
df_clean.to_parquet(f"pun_{year}.parquet", index=False)
print(f"Converted")





    
#DATA_DIR = Path("pun_data")
#files = sorted(DATA_DIR.glob("PUN_*.csv"))



"""
YEAR_PARQUET_DIR = Path("pun_data")
MASTER_PATH = Path("pun_master.parquet")

year_parquets = sorted(YEAR_PARQUET_DIR.glob("pun_*.parquet"))
if not year_parquets:
    raise FileNotFoundError(f"No yearly parquets found in {YEAR_PARQUET_DIR.resolve()}")

dfs = [pd.read_parquet(p) for p in year_parquets]
master = pd.concat(dfs, ignore_index=True).sort_values("datetime")

# Final safety: enforce numeric dtype + drop junk
master["pun"] = pd.to_numeric(master["pun"], errors="coerce")
master = master.dropna(subset=["datetime", "pun"])

# Final safety: deduplicate timestamps (if overlaps exist)
if not master["datetime"].is_unique:
    master = master.groupby("datetime", as_index=False)["pun"].mean().sort_values("datetime")

master.to_parquet(MASTER_PATH, index=False, engine="pyarrow")
print("Master saved:", MASTER_PATH.resolve())
print(master.dtypes)
print(master.head())
"""