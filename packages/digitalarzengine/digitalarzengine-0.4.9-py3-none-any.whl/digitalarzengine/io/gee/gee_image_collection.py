import traceback

import pandas as pd
import ee
from datetime import timedelta, datetime, date
from typing import Union, Optional, List

from digitalarzengine.io.gee.gee_image import GEEImage
from digitalarzengine.io.gee.gee_region import GEERegion
from enum import Enum


class CollectionOp(Enum):
    LATEST = "latest"
    OLDEST = "oldest"
    DATE = "date"
    NEAREST_DATE = "nearest_date"

    MEAN = "mean"
    MEDIAN = "median"
    SUM = "sum"
    TOTAL = "total"
    MIN = "min"
    MAX = "max"

    REDUCE = "reduce"
    TO_BANDS = "to_bands"


class GEEImageCollection:
    """
    Wrapper utilities for ee.ImageCollection providing:

    - Temporal filtering and selection (latest, oldest, date, nearest date)
    - Temporal reduction (mean, sum, min, max, reduce)
    - Safe conversion of ImageCollections to pandas DataFrames
      using chunked server-side reduction to avoid GEE 5000-feature limits
    - Resampling and aggregation helpers

    Designed for:
    - Daily datasets (e.g., CHIRPS, MODIS)
    - Hourly datasets (ERA5, GLDAS) using chunked retrieval
    """

    img_collection: ee.ImageCollection

    def __init__(self, img_coll: ee.ImageCollection):
        self.img_collection = img_coll

    @staticmethod
    def get_latest_image_collection(img_collection: ee.ImageCollection, limit: int = -1):
        """
        Sort an ImageCollection by time descending and optionally limit results.

        Parameters
        ----------
        img_collection : ee.ImageCollection
        limit : int, optional
            Number of latest images to keep. If <= 0, keeps all.

        Returns
        -------
        ee.ImageCollection
        """

        img_collection = img_collection.sort('system:time_start', False)
        if limit > 0:
            img_collection = img_collection.limit(limit)
        return img_collection

    @staticmethod
    def customize_collection(tags: str, dates: list) -> ee.ImageCollection:
        """
        Filters an ImageCollection to include only images whose acquisition dates
        match any of the dates provided in the list.

        Args:
            tags (str): ImageCollection ID.
            dates (list): List of date strings (e.g. ['2023-01-01', '2023-02-01']).

        Returns:
            ee.ImageCollection: Filtered image collection with daily images.
        """
        img_col = ee.ImageCollection(tags)

        # Convert Python date strings to ee.List of ee.Dates
        ee_dates = ee.List([ee.Date(date) for date in dates])

        def get_image_on_date(date):
            date = ee.Date(date)
            image = img_col.filterDate(date, date.advance(1, 'day')).first()
            return image

        filtered_images = ee_dates.map(get_image_on_date)

        # Wrap in ee.ImageCollection and filter nulls
        return ee.ImageCollection(filtered_images).filter(ee.Filter.notNull(['system:time_start']))

    @staticmethod
    def from_images(images: List[ee.Image]) -> ee.ImageCollection:
        """
        Build a GEEImageCollection from a Python list of ee.Image.
        """
        if not images:
            return ee.ImageCollection([])
        return ee.ImageCollection(images)

    @staticmethod
    def from_tags(cls, tag: str, date_range: tuple = None, region: Union[GEERegion, dict] = None):
        """
        Create a GEEImageCollection from a dataset tag with optional spatial
        and temporal filtering.

        Parameters
        ----------
        tag : str
            Earth Engine ImageCollection ID
            (e.g. 'COPERNICUS/S2_SR', 'UCSB-CHG/CHIRPS/DAILY')

        date_range : tuple(str, str), optional
            ('YYYY-MM-dd', 'YYYY-MM-dd') date range.
            End date is exclusive as per EE filterDate.

        region : GEERegion or dict, optional
            Spatial filter; if dict, interpreted as GeoJSON.

        Returns
        -------
        GEEImageCollection

        Example
        -------
        >>> ic = GEEImageCollection.from_tags(
        ...     'UCSB-CHG/CHIRPS/DAILY',
        ...     date_range=('2020-01-01', '2021-01-01'),
        ...     region=aoi
        ... )
        """

        # self.image_type = image_type
        img_collection = ee.ImageCollection(tag)
        if region is not None:
            region = GEERegion.from_geojson(region) if isinstance(region, dict) else region
            img_collection = img_collection.filterBounds(region.bounds)

        if date_range is not None:
            img_collection = img_collection.filterDate(date_range[0], date_range[1])
        return cls(img_collection)

    @staticmethod
    def get_collection_max_date(img_col: ee.ImageCollection) -> date:
        """
        Get the maximum acquisition date of an ImageCollection.

        Parameters
        ----------
        img_col : ee.ImageCollection

        Returns
        -------
        datetime.date
            Latest date present in the collection.
        """

        max_timestamp = img_col.aggregate_max('system:time_start')
        # max_timestamp = img_col.first().get('system:time_start')
        # Convert the timestamp to an ee.Date object (server-side)
        max_date = ee.Date(max_timestamp)

        # Format the date as a string (server-side)
        formatted_date = max_date.format('YYYY-MM-dd')
        # return formatted_date.getInfo()
        return datetime.strptime(formatted_date.getInfo(), "%Y-%m-%d").date()

    @staticmethod
    def get_latest_dates(image_collection: ee.ImageCollection,
                         delta_in_days: int = 10,
                         end_date: datetime = None) -> (str, str):
        """
        Compute a date range ending at the latest image in the collection.

        Parameters
        ----------
        image_collection : ee.ImageCollection
        delta_in_days : int
            Number of days before end_date.
        end_date : datetime, optional
            Override collection max date.

        Returns
        -------
        (str, str)
            ('YYYY-MM-dd', 'YYYY-MM-dd')
        """

        # Calculate the date range for the latest 10 days or any delta applied

        if end_date is None:
            end_date = GEEImageCollection.get_collection_max_date(image_collection)

        if end_date is None:
            end_date = datetime.utcnow().date()

        start_date = end_date - timedelta(days=delta_in_days)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

    @staticmethod
    def get_ymd_list(img_collection: ee.ImageCollection) -> list:
        """
        Extract unique acquisition dates (YYYY-MM-dd) from an ImageCollection.

        Uses system:time_start when available, otherwise falls back to system:index.

        Parameters
        ----------
        img_collection : ee.ImageCollection

        Returns
        -------
        list[str]
            Sorted unique date strings.
        """

        def iter_func(image, newList):
            image = ee.Image(image)
            newlist = ee.List(newList)

            # Use system:time_start if available
            date = ee.Algorithms.If(
                image.propertyNames().contains('system:time_start'),
                ee.Date(image.get('system:time_start')).format('YYYY-MM-dd'),
                # fallback: try to parse from system:index
                ee.String(image.get('system:index'))  # generic fallback
            )

            return newlist.add(date)

        return ee.List(img_collection.iterate(iter_func, ee.List([]))).distinct().sort().getInfo()

    # @staticmethod
    # def get_ymd_list(img_collection: ee.ImageCollection) -> list:
    #     # Inner Function: Processes each image in the collection
    #     def iter_func(image, newList):
    #         # Extract the image date as a YYYY-MM-dd string
    #         date = ee.String(image.date().format("YYYY-MM-dd"))
    #
    #         # Convert the existing list (newList) to an EE List for manipulation
    #         newlist = ee.List(newList)
    #
    #         # Add the current date to the list, sort the list, and return it
    #         return ee.List(newlist.add(date).sort())
    #
    #     # Apply the iteration to the image collection
    #     return img_collection.iterate(iter_func, ee.List([])).getInfo()

    def enumerate_collection(self):
        """
        Generator yielding (index, ee.Image) for each image
        in the ImageCollection (client-side enumeration).

        ⚠ Use only for small collections.

        Yields
        ------
        (int, ee.Image)
        """

        size = self.img_collection.size().getInfo()
        img_list = ee.List(self.img_collection.toList(self.img_collection.size()))
        for i in range(size):
            yield i, ee.Image(img_list.get(i))

    def info_ee_array_to_df(self,
                            region: GEERegion,
                            list_of_bands: list = None,
                            scale: int = None) -> pd.DataFrame:
        """
        Convert ee.ImageCollection.getRegion() output to a pandas DataFrame.

        Intended for point / very small region extraction.
        NOT suitable for large AOIs.

        Parameters
        ----------
        region : GEERegion
            Area of interest.
        list_of_bands : list[str], optional
            Bands to extract. Defaults to all bands.
        scale : int, optional
            Pixel resolution in meters.

        Returns
        -------
        pandas.DataFrame
            Columns: longitude, latitude, time, datetime, bands...
        """

        try:
            # Get first image in the collection
            gee_image = GEEImage(self.img_collection.first())

            # If list_of_bands is not provided, get all available bands
            list_of_bands = gee_image.get_band_names() if not list_of_bands else list_of_bands

            if not list_of_bands:  # If no bands are found, return an empty DataFrame
                return pd.DataFrame()

            if scale is None:
                region_area = region.aoi.area().getInfo()
                # Convert region area to linear meters (side length of a square)
                region_side = region_area ** 0.5
                min_scale, max_scale = gee_image.get_min_max_scale(list_of_bands)
                # Ensure scale is at least the pixel resolution and does not exceed the region's side length
                scale = min(min_scale, min(region_side, max_scale))
                # Fetch pixel data from Google Earth Engine
            arr = self.img_collection.getRegion(geometry=region.aoi, scale=scale).getInfo()

            # Ensure valid data is returned
            if not arr or len(arr) < 2:
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(arr)

            # Rearrange headers correctly
            headers = df.iloc[0].values
            df = pd.DataFrame(df.values[1:], columns=headers)

            # Convert numeric columns
            for band in list_of_bands:
                df[band] = pd.to_numeric(df[band], errors="coerce")

            # Convert time field into datetime format
            df["datetime"] = pd.to_datetime(df["time"], unit="ms")

            # Ensure relevant columns are retained
            df = df[["longitude", "latitude", "time", "datetime"] + list_of_bands]

            return df

        except Exception as e:
            print("Error in info_ee_array_to_df:", str(e))
            traceback.print_exc()
            return pd.DataFrame()

    @staticmethod
    def sum_resampler(coll: ee.ImageCollection, freq, unit, scale_factor, band_name):
        """
        This function aims to resample the time scale of an ee.ImageCollection.
        The function returns an ee.ImageCollection with the averaged sum of the
        band on the selected frequency.

        coll: (ee.ImageCollection) only one band can be handled
        freq: (int) corresponds to the resampling frequence
        unit: (str) corresponds to the resampling time unit.
                    must be 'day', 'month' or 'year'
        scale_factor (float): scaling factor used to get our value in the good unit
        band_name (str) name of the output band
        example:
        # Apply the resampling function to the precipitation dataset.
            pr_m = sum_resampler(pr, 1, "month", 1, "pr")
        # Apply the resampling function to the PET dataset.
            pet_m = sum_resampler(pet.select("PET"), 1, "month", 0.0125, "pet")
        # Combine precipitation and evapotranspiration.
            meteo = pr_m.combine(pet_m)

        """
        # Define initial and final dates of the collection.
        firstdate = ee.Date(
            coll.sort("system:time_start", True).first().get("system:time_start")
        )

        lastdate = ee.Date(
            coll.sort("system:time_start", False).first().get("system:time_start")
        )

        # Calculate the time difference between both dates.
        # https://developers.google.com/earth-engine/apidocs/ee-date-difference
        diff_dates = lastdate.difference(firstdate, unit)

        # Define a new time index (for output).
        new_index = ee.List.sequence(0, ee.Number(diff_dates), freq)

        # Define the function that will be applied to our new time index.
        def apply_resampling(date_index):
            # Define the starting date to take into account.
            startdate = firstdate.advance(ee.Number(date_index), unit)

            # Define the ending date to take into account according
            # to the desired frequency.
            enddate = firstdate.advance(ee.Number(date_index).add(freq), unit)

            # Calculate the number of days between starting and ending days.
            diff_days = enddate.difference(startdate, "day")

            # Calculate the composite image.
            image = (
                coll.filterDate(startdate, enddate)
                .mean()
                .multiply(diff_days)
                .multiply(scale_factor)
                .rename(band_name)
            )

            # Return the final image with the appropriate time index.
            return image.set("system:time_start", startdate.millis())

        # Map the function to the new time index.
        res = new_index.map(apply_resampling)

        # Transform the result into an ee.ImageCollection.
        res = ee.ImageCollection(res)

        return res

    def select_band(self, band: Union[str, list[str]]):
        """
        Select a specific band or list of bands from the current image collection.

        Parameters:
        - band (str or list of str): The name(s) of the band(s) to select.

        Example:
            self.select_band("NDVI")
            self.select_band(["NDVI", "EVI"])
        """
        if self.img_collection is None:
            raise ValueError("Image collection is not initialized.")

        self.img_collection = self.img_collection.select(band)

    @staticmethod
    def to_gee_img(ic: ee.ImageCollection, op: CollectionOp, *,
                   date: Optional[str] = None,
                   tolerance_days: int = 0,
                   reducer: Optional[ee.Reducer] = None) -> ee.Image:
        """
        Unified ImageCollection operator.

        Returns ee.Image.
        Usage:



            latest = GEEImageCollection.to_gee_img( chirps_ic, CollectionOp.LATEST)

            img_2020 = GEEImageCollection.to_gee_img(chirps_ic,
                CollectionOp.DATE,
                date="2020-03-01"
            )


            p10_p90 = GEEImageCollection.to_gee_img(chirps_ic,
                CollectionOp.REDUCE,
                reducer=ee.Reducer.percentile([10, 90])
            )

        """

        match op:

            # ------------------------
            # Single-image selectors
            # ------------------------
            case CollectionOp.LATEST:
                return ee.Image(ic.sort('system:time_start', False).first())

            case CollectionOp.OLDEST:
                return ee.Image(ic.sort('system:time_start', True).first())

            case CollectionOp.DATE:
                if not date:
                    raise ValueError("DATE operation requires 'date=YYYY-MM-dd'")
                d = ee.Date(date)
                return ee.Image(
                    ic.filterDate(d, d.advance(1, 'day'))
                    .sort('system:time_start', False)
                    .first()
                )

            case CollectionOp.NEAREST_DATE:
                if not date:
                    raise ValueError("NEAREST_DATE requires 'date=YYYY-MM-dd'")

                target = ee.Date(date)
                start = target.advance(-tolerance_days, 'day')
                end = target.advance(tolerance_days + 1, 'day')

                def add_dist(img):
                    img = ee.Image(img)
                    dist = ee.Number(img.get('system:time_start')) \
                        .subtract(target.millis()).abs()
                    return img.set('time_dist', dist)

                return ee.Image(
                    ic.filterDate(start, end)
                    .map(add_dist)
                    .sort('time_dist', True)
                    .first()
                )

            # ------------------------
            # Temporal reducers
            # ------------------------
            case CollectionOp.SUM | CollectionOp.TOTAL:
                return ee.Image(ic.sum())

            case CollectionOp.MEAN:
                return ee.Image(ic.mean())

            case CollectionOp.MEDIAN:
                return ee.Image(ic.median())

            case CollectionOp.SUM:
                return ee.Image(ic.sum())

            case CollectionOp.MIN:
                return ee.Image(ic.min())

            case CollectionOp.MAX:
                return ee.Image(ic.max())

            case CollectionOp.REDUCE:
                if reducer is None:
                    raise ValueError("REDUCE requires an ee.Reducer")
                return ee.Image(ic.reduce(reducer))

            case CollectionOp.TO_BANDS:
                return ee.Image(ic.toBands())

            case _:
                return ee.Image(ic.toBands())

            # case _:
            #     raise ValueError(f"Unsupported operation: {op}")

    @staticmethod
    def to_timeseries_df(
            ic: ee.ImageCollection,
            region: ee.Geometry,
            band: str,
            scale: int = 5500,
            reducer: Union[ee.Reducer, List[ee.Reducer], None] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            chunk_freq: str = "year",
            chunk_size: int = 1,
            max_features_per_pull: int = 4500,
    ) -> pd.DataFrame:
        """
        Convert an ee.ImageCollection into a pandas DataFrame time series by
        reducing each image over a region, using SAFE CHUNKED retrieval to
        avoid Earth Engine client-side feature limits (>5000 elements).

        This method is suitable for DAILY, HOURLY, or SUB-DAILY collections.

        Chunking is performed on the client side by splitting the time range
        into smaller intervals (year, month, week, or day) and fetching each
        chunk independently before concatenation.

        Parameters
        ----------
        ic : ee.ImageCollection
            Input ImageCollection (daily, hourly, etc.).

        region : ee.Geometry
            Area of interest used in reduceRegion.

        band : str
            Single band name to extract and reduce.

        scale : int, default=5500
            Pixel resolution (meters) for reduceRegion.

        reducer : ee.Reducer or list[ee.Reducer], optional
            Reducer(s) applied per image.
            If a list is provided, reducers are combined using sharedInputs=True.
            Example outputs:
                band_mean, band_p10, band_p90, band_max

        start_date : str, optional
            Inclusive start date ('YYYY-MM-dd' or ISO timestamp).
            If None, inferred from collection minimum time.

        end_date : str, optional
            Exclusive end date ('YYYY-MM-dd').
            If None, inferred from collection maximum time + 1 day.

        chunk_freq : {'year', 'month', 'week', 'day'}, default='year'
            Temporal unit used for chunking.
            Choose based on temporal resolution:
                - Daily data   → 'year'
                - Hourly data  → 'month' or 'week'
                - Sub-hourly   → 'day'

        chunk_size : int, default=1
            Number of chunk_freq units per chunk.
            Examples:
                chunk_freq='month', chunk_size=2 → 2-month chunks
                chunk_freq='week',  chunk_size=1 → weekly chunks

        max_features_per_pull : int, default=4500
            Safety guard to prevent client-side EEException.
            If a chunk exceeds this size, an error is raised with guidance.

        Returns
        -------
        pandas.DataFrame
            Time-sorted DataFrame with columns:
                - date (datetime64)
                - <band>_<reducer_output> (float)

        Notes
        -----
        - Uses reduceRegion per image (server-side).
        - Pulls FeatureCollections chunk-by-chunk via getInfo().
        - Deduplicates timestamps after concatenation.
        - Intended for time-series extraction, not spatial sampling.

        Examples
        --------
        Daily (CHIRPS):
        >>> df = GEEImageCollection.to_timeseries_df_chunked(
        ...     chirps_ic,
        ...     region=aoi,
        ...     band='precipitation',
        ...     reducer=[ee.Reducer.mean(), ee.Reducer.max()],
        ...     chunk_freq='year'
        ... )

        Hourly (ERA5):
        >>> df = GEEImageCollection.to_timeseries_df_chunked(
        ...     era5_ic,
        ...     region=aoi,
        ...     band='temperature_2m',
        ...     reducer=ee.Reducer.mean(),
        ...     chunk_freq='month'
        ... )

        Weekly chunks (very large collections):
        >>> df = GEEImageCollection.to_timeseries_df_chunked(
        ...     ic,
        ...     region=aoi,
        ...     band='ndvi',
        ...     reducer=ee.Reducer.mean(),
        ...     chunk_freq='week',
        ...     chunk_size=1
        ... )
        """

        # ---- reducer build
        if reducer is None:
            reducer = ee.Reducer.first()

        if isinstance(reducer, list):
            if len(reducer) == 0:
                reducer = ee.Reducer.first()
            else:
                r = reducer[0]
                for rr in reducer[1:]:
                    r = r.combine(rr, sharedInputs=True)
                reducer = r

        outputs = ee.List(ee.Reducer(reducer).getOutputs())

        def img_to_feat(img):
            img = ee.Image(img)
            date_str = ee.Date(img.get('system:time_start')).format("YYYY-MM-dd'T'HH:mm:ss")

            stats = img.select([band]).reduceRegion(
                reducer=reducer,
                geometry=region,
                scale=scale,
                maxPixels=1e13,
                tileScale=4
            )

            keys = outputs.map(lambda o: ee.String(band).cat('_').cat(ee.String(o)))
            values = keys.map(lambda k: stats.get(ee.String(k)))
            props = ee.Dictionary.fromLists(keys, values).set('date', date_str)
            return ee.Feature(None, props)

        def fetch_df_for_range(start_s: str, end_s: str) -> pd.DataFrame:
            ic_chunk = ic.filterDate(start_s, end_s)

            # optional safety check to avoid pulling too many features at once
            n = int(ic_chunk.size().getInfo())
            if n > max_features_per_pull:
                raise ValueError(
                    f"Chunk too large: {n} images/features in [{start_s}, {end_s}). "
                    f"Use smaller chunks (e.g. chunk_freq='week' or chunk_freq='day')."
                )

            fc = ee.FeatureCollection(ic_chunk.map(img_to_feat))
            info = fc.getInfo()
            feats = info.get('features', [])
            rows = [f.get('properties', {}) for f in feats]

            dfc = pd.DataFrame(rows)
            if dfc.empty:
                return dfc

            dfc['date'] = pd.to_datetime(dfc['date'])
            for c in dfc.columns:
                if c != 'date':
                    dfc[c] = pd.to_numeric(dfc[c], errors='coerce')
            return dfc

        # ---- bounds
        if start_date is None or end_date is None:
            t0 = ee.Date(ic.aggregate_min('system:time_start')).format('YYYY-MM-dd').getInfo()
            t1 = ee.Date(ic.aggregate_max('system:time_start')).format('YYYY-MM-dd').getInfo()
            if start_date is None:
                start_date = t0
            if end_date is None:
                end_date = (pd.to_datetime(t1) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')

        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        # ---- chunk iterator using pandas offsets
        freq_map = {
            "year": pd.DateOffset(years=chunk_size),
            "month": pd.DateOffset(months=chunk_size),
            "week": pd.DateOffset(weeks=chunk_size),
            "day": pd.DateOffset(days=chunk_size),
        }
        if chunk_freq not in freq_map:
            raise ValueError("chunk_freq must be one of: 'year','month','week','day'")

        step = freq_map[chunk_freq]

        dfs = []
        cur = start_dt
        while cur < end_dt:
            nxt = min(cur + step, end_dt)

            df_part = fetch_df_for_range(
                cur.strftime('%Y-%m-%d'),
                nxt.strftime('%Y-%m-%d')
            )
            if not df_part.empty:
                dfs.append(df_part)

            cur = nxt

        if not dfs:
            return pd.DataFrame()

        df = pd.concat(dfs, ignore_index=True).sort_values('date').reset_index(drop=True)
        df = df.drop_duplicates(subset=['date']).reset_index(drop=True)
        return df


