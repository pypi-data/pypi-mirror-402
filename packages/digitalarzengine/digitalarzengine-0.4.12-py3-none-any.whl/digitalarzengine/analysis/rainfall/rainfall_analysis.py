import calendar
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import ee
import numpy as np
import pandas as pd

from digitalarzengine.io.gee.gee_image_collection import GEEImageCollection
from digitalarzengine.pipeline.gee_pipeline import GEEPipeline


# Treat values below this as "trace/noise" and set to 0 before aggregation
TRACE_ZERO_MM = 0.3

class RainfallAnalysis:
    """
       CHIRPS daily rainfall summaries for an AOI (Madinah), exported to ONE Excel with sheets:
         - Meta
         - Annual
         - Monthly_Climatology
         - Monthly_Year_Matrix
         - Monthly_Dry_Days
         - Monthly_Wet_Days

       IMPORTANT: We apply TRACE_ZERO_MM CONSISTENTLY in ALL aggregation-based methods
                  so the sheets match each other.
    """
    gee_pipeline: Optional[GEEPipeline] = None

    def __init__(self, tag, scale=5500 ):
        """
        :param tag: "UCSB-CHG/CHIRPS/DAILY"
        :param scale: 5500
        """
        self.scale = scale
        self.tag = tag

    # -------------
    # Data Preparation: from GEE
    # -----------
    def get_image_collection(self, start_date, end_date=None):
        end_date = datetime.now().strftime("%Y-%m-%d") if end_date is None else end_date
        raw_ic = (
            ee.ImageCollection(self.tag)
            .filterDate(start_date, end_date)
            .filterBounds(self.gee_pipeline.region.bounds)
            .select("precipitation")
        )
        return raw_ic

    def get_daily_precipitation(self, start_date, end_date):
        """
        :param start_date:
        :param end_date:
        :return:
        """
        raw_ic = self.get_image_collection(start_date, end_date)
        reducers = [
            ee.Reducer.mean(),
            ee.Reducer.percentile([10, 90]),
            ee.Reducer.max(),
        ]

        aoi = self.gee_pipeline.region.get_aoi()
        df = GEEImageCollection.to_timeseries_df(
            raw_ic, region=aoi, band="precipitation", scale=5500, reducer=reducers
        )
        return df

    def average_annual_total_rainfall(
            self,
            start_year: int,
            end_year: Optional[int] = None,
            trace_threshold: float = TRACE_ZERO_MM,
    ) -> Dict[str, Any]:
        """
        Average annual total rainfall (mm/year) across selected years.

        For each year:
          - filter CHIRPS daily to that year
          - apply trace threshold daily (<thr => 0)
          - compute AOI mean rainfall per day (mm/day)
          - sum across days => annual total (mm/year)

        Then:
          - average annual totals across years

        Returns:
          {
            "avg_annual_total_mm_per_year": float|None,
            "years_used": "YYYY-YYYY",
            "n_years": int,
            "trace_threshold_mm_day": float,
            "annual_totals_mm": { "2016": 12.3, ... }   # optional but useful
          }
        """
        if end_year is None:
            end_year = start_year

        aoi = self.gee_pipeline.region.get_aoi()
        region_bounds = self.gee_pipeline.region.bounds
        thr = ee.Number(trace_threshold)

        def annual_total_feature(y):
            y = ee.Number(y).toInt()
            start = ee.Date.fromYMD(y, 1, 1)
            end = start.advance(1, "year")

            ic = (
                ee.ImageCollection(self.tag)
                .filterDate(start, end)
                .filterBounds(region_bounds)
                .select("precipitation")
            )

            # Apply trace threshold daily: P < thr => 0
            def apply_thr(img):
                img = ee.Image(img)
                p = img.select("precipitation")
                p_eff = p.where(p.lt(thr), 0).rename("precipitation")
                return p_eff.copyProperties(img, ["system:time_start"])

            ic_eff = ic.map(apply_thr)

            # AOI mean per day → Feature with mm_day
            def daily_mean_feat(img):
                img = ee.Image(img)
                mm_day = img.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=aoi,
                    scale=self.scale,
                    maxPixels=1e13,
                    tileScale=4
                ).get("precipitation")
                return ee.Feature(None, {"mm_day": mm_day})

            daily_fc = ee.FeatureCollection(ic_eff.map(daily_mean_feat))

            # annual total = sum of daily means
            annual_mm = ee.Number(daily_fc.aggregate_sum("mm_day"))

            return ee.Feature(None, {"year": y, "annual_mm": annual_mm})

        years_list = ee.List.sequence(int(start_year), int(end_year))
        annual_fc = ee.FeatureCollection(years_list.map(annual_total_feature))

        # Bring small result to client
        feats = annual_fc.getInfo().get("features", [])
        rows = [f["properties"] for f in feats]

        years_used = f"{start_year}-{end_year}"

        if not rows:
            return {
                "avg_annual_total_mm_per_year": None,
                "years_used": years_used,
                "n_years": 0,
                "trace_threshold_mm_day": trace_threshold,
                "annual_totals_mm": {},
                "note": "No data for selected years."
            }

        annual_df = pd.DataFrame(rows)
        annual_df["annual_mm"] = pd.to_numeric(annual_df["annual_mm"], errors="coerce")
        annual_df = annual_df.dropna(subset=["annual_mm"])

        n_years = int(annual_df["year"].nunique())
        avg_annual = float(annual_df["annual_mm"].mean()) if n_years else None

        annual_map = {str(int(r["year"])): float(r["annual_mm"]) for r in annual_df.to_dict("records")}

        return {
            "avg_annual_total_mm_per_year": avg_annual,
            "years_used": years_used,
            "n_years": n_years,
            "trace_threshold_mm_day": trace_threshold,
            "annual_totals_mm": annual_map,
        }

    # ----------------------------
    # QC: daily completeness
    # ----------------------------

    def quality_screen_daily(
        self, start_date: str, end_date: str,
        missing_threshold_pct: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Returns dict:
          expected_days, available_days, missing_days, missing_pct, confidence, missing_dates_sample
        """
        ic = self.get_image_collection(start_date, end_date)
        s = datetime.strptime(start_date, "%Y-%m-%d").date()
        e = datetime.strptime(end_date, "%Y-%m-%d").date()

        expected = []
        d = s
        while d < e:
            expected.append(d.strftime("%Y-%m-%d"))
            d += timedelta(days=1)

        available = GEEImageCollection.get_ymd_list(ic)  # client-side list
        expected_set = set(expected)
        available_set = set(available)

        missing = sorted(list(expected_set - available_set))

        expected_days = len(expected)
        available_days = len(available_set)
        missing_days = len(missing)
        missing_pct = (missing_days / expected_days * 100.0) if expected_days else 0.0
        confidence = "LOW" if missing_pct > missing_threshold_pct else "OK"

        return {
            "expected_days": expected_days,
            "available_days": available_days,
            "missing_days": missing_days,
            "missing_pct": missing_pct,
            "confidence": confidence,
            "missing_dates_sample": missing[:20],
        }

    def get_meta(self, start_date, end_date) -> pd.DataFrame:
        qc = self.quality_screen_daily(start_date, end_date)
        meta = {
            "indicator": "Rainfall Summaries (CHIRPS)",
            "dataset": "UCSB-CHG/CHIRPS/DAILY",
            "area": "Madinah Governorate",
            "period_start": start_date,
            "period_end": end_date,
            "scale_m": 5500,
            "reducers": "mean, p10, p90, max",
            "qc_expected_days": qc.get("expected_days"),
            "qc_available_days": qc.get("available_days"),
            "qc_missing_days": qc.get("missing_days"),
            "qc_missing_pct": qc.get("missing_pct"),
            "qc_confidence": qc.get("confidence"),
            "note": f"Daily rainfall < {TRACE_ZERO_MM} mm/day treated as 0 for ALL aggregations.",
        }
        meta_df = pd.DataFrame({"key": list(meta.keys()), "value": list(meta.values())})
        return meta_df


    # ----------------------------
    # Helper: apply trace threshold
    # ----------------------------
    @staticmethod
    def apply_trace_threshold(series: pd.Series, trace_threshold: float = TRACE_ZERO_MM) -> pd.Series:
        """
        Treat values < trace_threshold as 0 (trace/noise).
        """
        return series.where(series >= trace_threshold, 0.0)

    @staticmethod
    def _prep_df(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
        """
        Standard prep: parse date + numeric + dropna + sort.
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        df = df.dropna(subset=[value_col]).sort_values("date").reset_index(drop=True)
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        return df

    # ------------------------
    # Raster:
    # ------------------------
    def get_annual_total_image(self, year: int, trace_threshold: float = TRACE_ZERO_MM) -> ee.Image:
        """
        Calculates total annual precipitation as a single ee.Image for a given year.

        :param year: The year to calculate (e.g., 2023)
        :param trace_threshold: Minimum mm/day to consider (values below set to 0)
        :return: ee.Image with a single band 'precipitation' representing mm/year
        """
        start_date = ee.Date.fromYMD(year, 1, 1)
        end_date = start_date.advance(1, "year")
        thr = ee.Number(trace_threshold)

        # 1. Filter the collection
        ic = (
            ee.ImageCollection(self.tag)
            .filterDate(start_date, end_date)
            .filterBounds(self.gee_pipeline.region.bounds)
            .select("precipitation")
        )

        # 2. Apply trace threshold pixel-wise: If pixel < threshold, set to 0
        def mask_trace_noise(img):
            p = img.select("precipitation")
            # Using .where() to zero out values below threshold
            p_eff = p.where(p.lt(thr), 0)
            return p_eff.copyProperties(img, ["system:time_start"])

        ic_eff = ic.map(mask_trace_noise)

        # 3. Reduce by Sum to get total mm for the year
        annual_total_img = ic_eff.sum().rename(f"total_precipitation_{year}")

        return annual_total_img

    def get_average_monthly_total_image(
            self,
            month: int,
            start_year: int,
            end_year: int,
            trace_threshold: float = TRACE_ZERO_MM
    ) -> ee.Image:
        """
        Calculates the mean total rainfall for a specific month across a range of years.

        Example: If month=1, it finds the sum of Jan 2016, sum of Jan 2017...
        and returns the average of those sums.
        """
        years = ee.List.sequence(start_year, end_year)
        thr = ee.Number(trace_threshold)

        def get_monthly_sum(y):
            y = ee.Number(y).toInt()
            # Filter to the specific month of the specific year
            start = ee.Date.fromYMD(y, month, 1)
            end = start.advance(1, "month")

            ic = (
                ee.ImageCollection(self.tag)
                .filterDate(start, end)
                .select("precipitation")
            )

            # Apply trace threshold pixel-wise before summing
            def apply_thr(img):
                return img.where(img.lt(thr), 0).copyProperties(img, ["system:time_start"])

            # Sum the daily effective rainfall for this month/year
            return ic.map(apply_thr).sum().set("year", y)

        # 1. Create a collection of "Monthly Totals" (one image per year)
        monthly_totals_col = ee.ImageCollection.fromImages(years.map(get_monthly_sum))

        # 2. Average those monthly totals across all years
        avg_monthly_img = monthly_totals_col.mean().rename(
            f"avg_total_precip_month_{month}_{start_year}_{end_year}"
        )

        return avg_monthly_img

    # ----------------------------
    # Summaries (CONSISTENT threshold)
    # ----------------------------
    @staticmethod
    def annual_rainfall_totals(
            df: pd.DataFrame,
            value_col: str,
            *,
            trace_threshold: float = TRACE_ZERO_MM,
    ) -> pd.DataFrame:
        df = RainfallAnalysis._prep_df(df, value_col)
        df["P_eff"] = RainfallAnalysis.apply_trace_threshold(df[value_col], trace_threshold)

        annual = (
            df.groupby("year", as_index=False)["P_eff"]
            .sum()
            .rename(columns={"P_eff": "annual_rainfall_mm"})
        )
        return annual

    @staticmethod
    def monthly_climatology_named(
            df: pd.DataFrame,
            value_col: str,
            *,
            trace_threshold: float = TRACE_ZERO_MM,
    ) -> pd.DataFrame:
        """
        Monthly climatology: mean monthly total across years.
        Threshold applied to daily values BEFORE monthly aggregation.
        """
        df = RainfallAnalysis._prep_df(df, value_col)
        df["P_eff"] = RainfallAnalysis.apply_trace_threshold(df[value_col], trace_threshold)

        # Monthly totals per year (effective rainfall)
        monthly_yearly = df.groupby(["year", "month"], as_index=False)["P_eff"].sum()

        # Mean across years for each month
        clim = (
            monthly_yearly.groupby("month", as_index=False)["P_eff"]
            .mean()
            .rename(columns={"P_eff": "mean_monthly_rainfall_mm"})
        )
        clim["month_name"] = clim["month"].apply(lambda m: calendar.month_abbr[m])
        return clim[["month", "month_name", "mean_monthly_rainfall_mm"]]

    @staticmethod
    def monthly_year_rf_matrix(
            df: pd.DataFrame,
            value_col: str,
            *,
            trace_threshold: float = TRACE_ZERO_MM,
    ) -> pd.DataFrame:
        """
        Year x Month rainfall totals matrix (mm).
        Threshold applied to daily values BEFORE monthly aggregation.
        """
        df = RainfallAnalysis._prep_df(df, value_col)
        df["P_eff"] = RainfallAnalysis.apply_trace_threshold(df[value_col], trace_threshold)

        monthly = df.groupby(["year", "month"], as_index=False)["P_eff"].sum()

        matrix = (
            monthly.pivot(index="year", columns="month", values="P_eff")
            .sort_index()
            .rename(columns=lambda m: calendar.month_abbr[int(m)])
        )

        matrix.index.name = "year"  # ensure index is named
        return matrix.reset_index()  # year becomes a normal column

    @staticmethod
    def monthly_daycount_matrix(
        df: pd.DataFrame,
        value_col: str,
        *,
        threshold: float = TRACE_ZERO_MM,
        day_type: str = "dry",  # "dry" or "wet"
    ) -> pd.DataFrame:
        """
        Monthly x Year day-count matrix:
          - dry: count days with P < threshold
          - wet: count days with P >= threshold
        """
        if day_type not in {"dry", "wet"}:
            raise ValueError("day_type must be 'dry' or 'wet'")

        df = RainfallAnalysis._prep_df(df, value_col)

        if day_type == "dry":
            df["flag"] = (df[value_col] < threshold).astype(int)
        else:
            df["flag"] = (df[value_col] >= threshold).astype(int)

        counts = df.groupby(["year", "month"], as_index=False)["flag"].sum().rename(columns={"flag": "days"})
        # matrix = counts.pivot(index="month", columns="year", values="days").fillna(0).astype(int)
        # matrix = matrix.sort_index()
        #
        # matrix.insert(0, "Month", [calendar.month_abbr[m] for m in matrix.index])
        # return matrix.reset_index(drop=True)
        matrix = (
            counts.pivot(index="year", columns="month", values="days")
            .sort_index()
            .rename(columns=lambda m: calendar.month_abbr[int(m)])
        )

        matrix.index.name = "year"  # ensure index is named
        return matrix.reset_index()  # year becomes a normal column


    @staticmethod
    def monthly_percentile_thresholds(
            df: pd.DataFrame,
            value_col: str,
            *,
            trace_threshold: float = TRACE_ZERO_MM,
            p_low: float = 10.0,
            p_high: float = 90.0,
            wet_only: bool = False,
    ) -> pd.DataFrame:
        """
        Month-wise TEMPORAL percentile thresholds (across days) from a daily timeseries df.
        Returns exactly 12 rows (months 1..12) with p10_mm and p90_mm as columns.
        """

        dfx = RainfallAnalysis._prep_df(df, value_col=value_col)
        dfx["P_eff"] = RainfallAnalysis.apply_trace_threshold(dfx[value_col], trace_threshold)

        # counts from FULL series (for reporting)
        counts = (
            dfx.groupby("month", as_index=False)
            .agg(
                n_days=("P_eff", "size"),
                n_wet_days=("P_eff", lambda s: int((s > 0).sum())),
            )
        )

        # percentile calc series (optionally wet days only)
        dfx_calc = dfx[dfx["P_eff"] > 0].copy() if wet_only else dfx.copy()

        q_low = p_low / 100.0
        q_high = p_high / 100.0

        # Compute quantiles in a stable way -> wide columns
        qs = (
            dfx_calc.groupby("month")["P_eff"]
            .quantile([q_low, q_high])  # produces MultiIndex: (month, quantile)
            .unstack(level=-1)  # columns become quantiles
            .rename(columns={q_low: "p10_mm", q_high: "p90_mm"})
            .reset_index()
        )

        out = counts.merge(qs, on="month", how="left")
        out["month_name"] = out["month"].apply(lambda m: calendar.month_abbr[int(m)])

        out = out.sort_values("month")[["month", "month_name", "n_days", "n_wet_days", "p10_mm", "p90_mm"]]
        return out.reset_index(drop=True)


    @staticmethod
    def classify_abnormal_days(
        df: pd.DataFrame,
        value_col: str,
        thresholds_monthly: pd.DataFrame,
        *,
        trace_threshold: float = TRACE_ZERO_MM,
    ) -> pd.DataFrame:
        """
        Adds P_eff, p10_mm, p90_mm and ARD flags to each daily row.

        Returns daily dataframe with columns:
          date, year, month, P_eff, p10_mm, p90_mm, is_AWD, is_ADD, ARD_code, ARD_label
        """

        dfx = RainfallAnalysis._prep_df(df, value_col=value_col)
        dfx["P_eff"] = RainfallAnalysis.apply_trace_threshold(dfx[value_col], trace_threshold)

        # Keep only the columns needed for join
        thr = thresholds_monthly[["month", "p10_mm", "p90_mm"]].copy()

        # Join thresholds by month
        dfx = dfx.merge(thr, on="month", how="left")

        # Flag abnormal days
        dfx["is_AWD"] = dfx["P_eff"] > dfx["p90_mm"]
        dfx["is_ADD"] = dfx["P_eff"] < dfx["p10_mm"]

        # Encode ARD: -1 dry, +1 wet, 0 normal
        # (If both true due to NaNs or weirdness, prioritize AWD)
        dfx["ARD_code"] = np.select(
            [dfx["is_AWD"], dfx["is_ADD"]],
            [1, -1],
            default=0
        )

        dfx["ARD_label"] = dfx["ARD_code"].map({1: "AWD", 0: "Normal", -1: "ADD"})

        # Return a tidy set of columns (add more if you want)
        return dfx[[
            "date", "year", "month",
            value_col, "P_eff",
            "p10_mm", "p90_mm",
            "is_ADD", "is_AWD",
            "ARD_code", "ARD_label"
        ]].sort_values("date").reset_index(drop=True)


if __name__ == "__main__":
    ### need to create pipline first
    rf_analysis = RainfallAnalysis("UCSB-CHG/CHIRPS/DAILY", scale=5500)
    start_date = "2016-01-01"
    end_date = "2025-12-31"
    df = rf_analysis.get_daily_precipitation(start_date, end_date)
    value_col = "precipitation_mean" # col name in the df
    trace_threshold = 0.2
    annual_df = rf_analysis.annual_rainfall_totals(df, value_col=value_col, trace_threshold=trace_threshold)
    monthly_df = rf_analysis.monthly_climatology_named(df, value_col=value_col, trace_threshold=trace_threshold)
    matrix_df = rf_analysis.monthly_year_matrix(df, value_col=value_col, trace_threshold=trace_threshold)
    dry_df = rf_analysis.monthly_daycount_matrix(df, value_col=value_col, threshold=trace_threshold,
                                                      day_type="dry")
    wet_df = rf_analysis.monthly_daycount_matrix(df, value_col=value_col, threshold=trace_threshold,
                                                      day_type="wet")

    ### Abnormal days calculation
    thresholds_all = rf_analysis.monthly_percentile_thresholds(df, "precipitation_max")
    print("Monthly percentile thresholds:", thresholds_all.head(12))

    daily_ard = rf_analysis.classify_abnormal_days(
        df,
        value_col="precipitation_mean",
        thresholds_monthly=thresholds_all,
        trace_threshold=0.2
    )

    awd_days = daily_ard[daily_ard["is_AWD"]].copy()
    print(awd_days[["date", "P_eff", "p90_mm", "month"]].head(20))

