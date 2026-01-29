
import os
import re
import traceback
from pathlib import Path
import folium
import rasterio
import matplotlib.cm as cm
import matplotlib.colors as colors
import base64
import io
import webbrowser
import tempfile

from geopandas import GeoDataFrame
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from rasterio import DatasetReader, Env
from rasterio.merge import merge
from scipy.stats import genextreme
from typing import List, Optional, Sequence, Union, Dict, Any
import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio.mask import mask

from digitalarzengine.io.file_io import FileIO
from digitalarzengine.io.rio_raster import RioRaster
from digitalarzengine.utils.singletons import da_logger


class RioProcess:

    @staticmethod
    def read_raster_ds(img_folder: str):
        ds_files: [DatasetReader] = []
        path = Path(img_folder)
        issues_folder = os.path.join(img_folder, "issue_in_files")
        os.makedirs(issues_folder,exist_ok=True)
        # count = FileIO.get_file_count(img_folder)
        # test = [str(p) for p in path.iterdir() if p.suffix == ".tif"]
        # ds_files = []
        for p in path.iterdir():
            if p.suffix == ".tif":
                try:
                    ds_files.append(RioRaster(str(p)).get_dataset())
                except Exception as e:
                    traceback.print_exc()
                    print(str(e))
                    FileIO.mvFile(str(p), issues_folder)
        return ds_files

    @classmethod
    def mosaic_images(cls, img_folder: str = None, ds_files: [DatasetReader] = (),  ext="tif") -> RioRaster:
        is_limit_changed = False
        if img_folder is not None:
            # count = FileIO.get_file_count(img_folder)
            count = FileIO.get_file_count(img_folder)
            # get file reading limits
            soft, hard = FileIO.get_file_reading_limit()
            # print("soft", soft, "hard", hard)
            if count > soft:
                if count * 2 < hard:
                    """
                    default limit is  soft: 12544 hard:9223372036854775807
                    """
                    FileIO.set_file_reading_limit(count * 2)

                    is_limit_changed = True
                else:
                    raise IOError(f"you are trying to read {count} files. Cannot read more than {hard} files.")
            ds_files = cls.read_raster_ds(img_folder)
            # problem_files.append(str(p))
        if len(ds_files) > 0:
            with Env(CHECK_DISK_FREE_SPACE=False):
                mosaic, out_trans = merge(ds_files)
                crs = ds_files[0].crs
                raster = RioRaster.raster_from_array(mosaic, crs=crs, g_transform=out_trans)
            if is_limit_changed:
                FileIO.set_file_reading_limit(soft)
            return raster

    @staticmethod
    def get_return_period_surfaces(raster: RioRaster, output_path, return_periods=(2, 5, 10, 25, 50, 100)):

        data = raster.get_data_array()
        no_datavalue = raster.get_nodata_value()

        # Prepare output array (bands = number of return periods, height, width)
        return_level_raster = np.full((len(return_periods), data.shape[1], data.shape[2]), no_datavalue,
                                      dtype=np.float32)

        # GEV Fit for each pixel
        for i in range(data.shape[1]):  # Loop over rows
            for j in range(data.shape[2]):  # Loop over columns
                pixel_values = data[:, i, j]  # Extract yearly max precipitation for this pixel

                # Exclude nodata values
                valid_values = pixel_values[pixel_values != no_datavalue]

                if valid_values.size == 0 or np.all(np.isnan(valid_values)):  # Skip if no valid values
                    continue

                # Fit GEV distribution (shape, location, scale)
                shape, loc, scale = genextreme.fit(valid_values)

                # Compute return level for each return period
                for band_idx, rp in enumerate(return_periods):
                    return_level_raster[band_idx, i, j] = genextreme.ppf(1 - 1 / rp, shape, loc=loc, scale=scale)

        # Save the single raster with multiple bands

        profile = raster.get_profile().copy()
        profile.update(dtype=rasterio.float32, count=len(return_periods),
                       nodata=no_datavalue)  # Ensure nodata value is set

        with rasterio.open(output_path, "w", **profile) as dst:
            for band_idx, rp in enumerate(return_periods):
                dst.write(return_level_raster[band_idx], band_idx + 1)  # Write each return period to a band
                dst.set_band_description(band_idx + 1, f"Return Period {rp} years")  # Set band name

            dst.update_tags(return_periods=str(return_periods))  # Store metadata

        print(f"Saved: {output_path}")

    @staticmethod
    def _extent_from_transform(transform, width, height):
        xmin = transform.c
        ymax = transform.f
        xmax = xmin + transform.a * width
        ymin = ymax + transform.e * height
        # normalize so (xmin, xmax, ymin, ymax)
        return (min(xmin, xmax), max(xmin, xmax), min(ymin, ymax), max(ymin, ymax))

    from typing import Optional, Sequence, Union

    from typing import Optional, Sequence, Union, Dict, Any
    import numpy as np
    import matplotlib.pyplot as plt
    from geopandas import GeoDataFrame
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    # ...

    @staticmethod
    def create_collage_images(
            raster: RioRaster,
            title: str,
            output_fp: str,
            no_of_rows: int = 2,
            cmap: str = 'Blues',
            edgecolor: str = 'green',
            linewidth: float = 1.0,
            gdf: Optional[GeoDataFrame] = None,
            sub_titles: Optional[Sequence[str]] = None,
            vmin: Optional[Union[float, str]] = None,
            vmax: Optional[Union[float, str]] = None,

            band_names: Optional[Sequence[Union[int, str]]] = None,
            band_titles: Optional[Sequence[str]] = None,

            # ✅ NEW: labeling controls
            label_field: Optional[str] = None,  # e.g. "name" / "id"
            label_style: Optional[Dict[str, Any]] = None,  # matplotlib text kwargs
            label_min_dist_px: int = 18,  # declutter threshold (pixels)
            label_max_count: Optional[int] = None,  # cap labels per subplot
            label_only_largest: bool = False,  # label largest polys first
    ):
        """
        Create a multi-band image collage for a raster.

        This function visualizes each band of a raster in a grid layout. Bands are
        rendered using a shared colormap, optional vector boundaries, optional
        vector labels with automatic decluttering, and per-band color limits
        (absolute or percentile-based).

        Parameters
        ----------
        raster : RioRaster
            Raster object providing bands, metadata, transform, CRS, and nodata.
        title : str
            Main title prefix applied to each subplot (band name appended).
        output_fp : str
            Destination file path for the saved image (PNG, JPG, etc.).
        no_of_rows : int, default=2
            Number of rows in the figure grid. Columns are computed automatically.
        cmap : str, default='Blues'
            Matplotlib colormap name.
        edgecolor : str, default='green'
            Boundary color for overlaying vector geometries (if provided).
        linewidth : float, default=1.0
            Line thickness for vector boundaries.
        gdf : GeoDataFrame, optional
            Vector layer to plot on top of each band. Reprojected if CRS differs.
        sub_titles : Sequence[str], optional
            Custom subtitles for each band. Falls back to raster band names.
        vmin : float or str, optional
            Lower limit for color scaling. Can be:
                - a float (absolute value), e.g. 0
                - a percentile string, e.g. "5%" or "2.5%"
            Percentiles are computed **per band** ignoring nodata.
        vmax : float or str, optional
            Upper limit for color scaling. Same rules as `vmin`.

        band_names : sequence of int or str, optional
                Bands to include in the collage.
                - int values refer to 1-based band indices
                - str values refer to raster band names
                If None, all bands are plotted.

        band_titles : sequence of str, optional
                Custom titles for each plotted band (in plotting order).
                If provided, these override raster band names.
                If fewer titles than bands are given, remaining bands fall back
                to raster.get_band_name().


        Labeling Parameters
        -------------------
        label_field : str, optional
            Column name in `gdf` containing text labels to draw on the map.
            If None, no labels are rendered.
        label_style : dict, optional
            Matplotlib text style keyword arguments passed to `ax.text`.
            Defaults include:
                - fontsize=9
                - color="black"
                - centered alignment
                - semi-transparent white background box
        label_min_dist_px : int, default=18
            Minimum pixel distance between labels used for decluttering.
            Larger values result in fewer labels.
        label_max_count : int, optional
            Maximum number of labels drawn per subplot. Useful for very dense layers.
        label_only_largest : bool, default=False
            If True and geometries are polygons, labels are placed on the
            largest features first (by area).

        Notes
        -----
        - Each raster band is plotted in its own subplot.
        - Nodata values are converted to NaN and rendered using the colormap's
          "bad" color (white).
        - Percentile-based `vmin` / `vmax` values are computed independently
          for each band.
        - Vector labels are placed using representative points (polygons)
          or centroids (lines/points).
        - Label decluttering is performed in **pixel space**, ensuring consistent
          spacing regardless of map scale.
        - Subplots exceeding the number of raster bands are hidden automatically.

        Returns
        -------
        str
            The same `output_fp` provided, after saving the figure.

        Examples
        --------
        # Absolute color limits
        create_collage_images(
            raster,
            "My Raster",
            "out.png",
            vmin=0,
            vmax=500
        )

        # Percentile stretch (per band)
        create_collage_images(
            raster,
            "My Raster",
            "out.png",
            vmin="2%",
            vmax="98%",
            band_names=[1, 3, 5]
        )
        create_collage_images(
            raster,
            "Indices",
            "out.png",
            band_names=["B4", "B8", "NDVI"],
            band_titles=["Red", "NIR", "NDVI"]
        )


        # Mixed: fixed lower bound + percentile upper bound
        create_collage_images(
            raster,
            "My Raster",
            "out.png",
            vmin=0,
            vmax="99%"
        )

        # Raster collage with vector boundaries and decluttered labels
        create_collage_images(
            raster,
            "My Raster",
            "out.png",
            gdf=my_gdf,
            label_field="NAME",
            label_min_dist_px=22,
            label_max_count=80,
            label_style={"fontsize": 8}
        )
        """

        def _resolve_limit(limit: Optional[Union[float, str]], band: np.ndarray):
            if limit is None:
                return None
            if isinstance(limit, str) and limit.endswith('%'):
                try:
                    p = float(limit[:-1])
                except ValueError:
                    raise ValueError(f"Invalid percentile string for vmin/vmax: {limit!r}")
                return float(np.nanpercentile(band, p))
            return float(limit)

        def _label_points_for_geoms(gdf_: GeoDataFrame) -> np.ndarray:
            """
            Returns Nx2 array of label (x,y) positions in data coords.
            Use representative_point for polygons (always inside), centroid for others.
            """
            geom_type = gdf_.geometry.geom_type
            # representative_point works great for polygons; for lines it gives a point on the line too,
            # but centroid is fine for most. We'll choose representative_point for anything area-ish.
            use_rep = geom_type.isin(["Polygon", "MultiPolygon"]).to_numpy()
            pts = []
            for use_rp, geom in zip(use_rep, gdf_.geometry):
                if geom is None or geom.is_empty:
                    pts.append((np.nan, np.nan))
                    continue
                p = geom.representative_point() if use_rp else geom.centroid
                pts.append((p.x, p.y))
            return np.asarray(pts, dtype=float)

        def _declutter_and_draw_labels(
                ax,
                gdf_: GeoDataFrame,
                label_field_: str,
                *,
                min_dist_px: int,
                max_count: Optional[int],
                style: Dict[str, Any],
                only_largest: bool,
        ):
            if gdf_ is None or gdf_.empty:
                return
            if label_field_ not in gdf_.columns:
                raise ValueError(f"label_field={label_field_!r} not found in gdf columns.")

            # take rows with non-null labels & valid geometry
            gg = gdf_.loc[gdf_[label_field_].notna() & gdf_.geometry.notna()].copy()
            if gg.empty:
                return

            # optional: label largest polygons first (helps readability)
            if only_largest:
                try:
                    gg["_area_tmp"] = gg.geometry.area
                    gg = gg.sort_values("_area_tmp", ascending=False)
                except Exception:
                    pass

            # compute candidate positions
            xy = _label_points_for_geoms(gg)
            labels = gg[label_field_].astype(str).to_numpy()

            # convert to display coords (pixels) for decluttering
            disp = ax.transData.transform(xy)  # Nx2
            keep = []
            kept_disp = []

            # greedy keep: accept point if far enough from all already kept points
            for idx, (dxy, lab, dpos) in enumerate(zip(xy, labels, disp)):
                if not np.isfinite(dxy).all() or not np.isfinite(dpos).all():
                    continue

                if max_count is not None and len(keep) >= max_count:
                    break

                if not kept_disp:
                    keep.append((dxy[0], dxy[1], lab))
                    kept_disp.append(dpos)
                    continue

                # min distance to existing labels in pixel space
                diffs = np.asarray(kept_disp) - dpos
                dist2 = np.sum(diffs * diffs, axis=1)
                if np.min(dist2) >= (min_dist_px ** 2):
                    keep.append((dxy[0], dxy[1], lab))
                    kept_disp.append(dpos)

            # draw
            for x, y, lab in keep:
                ax.text(x, y, lab, **style)

        sub_titles = [] if sub_titles is None else list(sub_titles)

        # --- resolve band indices to plot ---
        all_band_indices = list(range(1, raster.get_spectral_resolution() + 1))

        if band_names is None:
            bands_to_plot = all_band_indices
        else:
            bands_to_plot = []
            for b in band_names:
                if isinstance(b, int):
                    if b < 1 or b > len(all_band_indices):
                        raise ValueError(f"Invalid band index: {b}")
                    bands_to_plot.append(b)
                elif isinstance(b, str):
                    matched = False
                    for i in all_band_indices:
                        if raster.get_band_name(i) == b:
                            bands_to_plot.append(i)
                            matched = True
                            break
                    if not matched:
                        raise ValueError(f"Band name '{b}' not found in raster.")
                else:
                    raise TypeError("band_names must contain int or str values.")

        no_of_bands = len(bands_to_plot)

        # no_of_bands = raster.get_spectral_resolution()
        no_of_cols = no_of_bands // no_of_rows if (no_of_bands % no_of_rows == 0) else int(
            np.ceil(no_of_bands / no_of_rows))

        fig, axes = plt.subplots(
            no_of_rows,
            no_of_cols,
            figsize=(5 * no_of_cols, 4 * no_of_rows),
            constrained_layout=True
        )
        axes = axes.ravel() if isinstance(axes, np.ndarray) else np.array([axes])

        raster_crs = raster.get_crs()
        transform = raster.get_geo_transform()
        nodata_value = raster.get_nodata_value()

        if gdf is not None and not gdf.empty and getattr(gdf, "crs", None) is not None:
            if gdf.crs != raster_crs:
                gdf = gdf.to_crs(raster_crs, inplace=False)

        cmap_obj = plt.get_cmap(cmap).copy()
        cmap_obj.set_bad(color='white')

        # ✅ default label style (can be overridden via label_style)
        default_label_style = dict(
            fontsize=9,
            color="black",
            ha="center",
            va="center",
            zorder=10,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.65),
        )
        if label_style:
            default_label_style.update(label_style)

        # for i in range(no_of_bands):
        #     band = raster.get_data_array(i + 1).astype(float)
        for plot_idx, band_idx in enumerate(bands_to_plot):
            band = raster.get_data_array(band_idx).astype(float)

            if nodata_value is not None:
                band[band == nodata_value] = np.nan

            h, w = band.shape
            extent = RioProcess._extent_from_transform(transform, w, h)

            vmin_resolved = _resolve_limit(vmin, band)
            vmax_resolved = _resolve_limit(vmax, band)

            # ax = axes[i]
            ax = axes[plot_idx]
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.1)

            im = ax.imshow(
                band,
                cmap=cmap_obj,
                interpolation='nearest',
                extent=extent,
                origin='upper',
                vmin=vmin_resolved,
                vmax=vmax_resolved,
            )

            if gdf is not None and not gdf.empty:
                gdf.boundary.plot(ax=ax, edgecolor=edgecolor, linewidth=linewidth)

                # ✅ NEW: draw labels (decluttered)
                if label_field:
                    _declutter_and_draw_labels(
                        ax,
                        gdf,
                        label_field,
                        min_dist_px=label_min_dist_px,
                        max_count=label_max_count,
                        style=default_label_style,
                        only_largest=label_only_largest,
                    )

            # band_title = sub_titles[i] if (sub_titles and i < len(sub_titles)) else raster.get_band_name(i + 1)

            # normalize titles (priority: band_titles > sub_titles > raster band name)
            if band_titles is not None:
                band_titles = list(band_titles)
            elif sub_titles is not None:
                band_titles = list(sub_titles)
            else:
                band_titles = []

            band_title = (
                band_titles[plot_idx]
                if band_titles and plot_idx < len(band_titles)
                else raster.get_band_name(band_idx)
            )

            ax.set_title(f"{title} – {band_title}" if title else band_title)
            ax.set_xticks([])
            ax.set_yticks([])

            fig.colorbar(im, cax=cax)

        for j in range(no_of_bands, len(axes)):
            axes[j].set_visible(False)

        fig.savefig(output_fp, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_fp

    # @staticmethod
    # def create_collage(self, bands, rp, aoi_gdf: GeoDataFrame):
    #     # band_data = np.asarray(list(bands.values()))
    #     height, width = bands[f"Runoff_volume_return_period_{rp}_year"].shape
    #     band_data = []
    #     sub_titles = []
    #     for value, data in bands.items():
    #         data = cv2.resize(data, (width, height), interpolation=cv2.INTER_LINEAR)
    #         print(value, data.shape)
    #         band_data.append(data)
    #         sub_titles.append(value.replace("_", " "))
    #     band_data = np.asarray(band_data)
    #     print(band_data.shape)
    #     fp = self.get_raster_fp(rp, "surplus_water")
    #
    #     # cat_level_7_gdv = AOIUtils.get_catchment_boundary_data(level=7)
    #     # cat_level_7_gdv = GPDVector.multipolygon_to_polygon(cat_level_7_gdv)
    #     # cat_level_7_gdv = cat_level_7_gdv.spatial_join(input_gdf=self.aoi_gdf, predicate='within')
    #
    #     ref_raster = RioRaster(fp)
    #     raster = ref_raster.rio_raster_from_array(band_data)
    #     out_collage = os.path.join(os.path.dirname(fp), f"collage/runoff_analysis_{rp}_rp.jpg")
    #     os.makedirs(os.path.dirname(out_collage), exist_ok=True)
    #     RioProcess.create_collage_images(raster, "", out_collage, no_of_rows=2, gdf=cat_level_7_gdv,
    #                                      sub_titles=sub_titles)
    #     print("collage created at ", out_collage)

    @staticmethod
    def stack_rasters_in_memory(
            sources: Sequence[Union['RioRaster', np.ndarray]],
            reference: 'RioRaster' = None,
            band_names: List[str] = None,
            resampling: str = "nearest"
    ) -> 'RioRaster':
        """
        Align and stack sources into a new multiband *in-memory* RioRaster.
        If 'reference' is None, the first element of 'sources' is used as the grid/CRS reference.
        """

        def _as_raster_like(ref_for_meta: 'RioRaster', x) -> 'RioRaster':
            if isinstance(x, RioRaster):
                return x
            # If it's a numpy array, we need a reference to give it a CRS/Transform
            arr = x if x.ndim in (2, 3) else np.asarray(x)
            return RioRaster.raster_from_array(
                img_arr=arr,
                crs=ref_for_meta.get_crs(),
                g_transform=ref_for_meta.get_geo_transform(),
                nodata_value=ref_for_meta.get_nodata_value()
            )

        def _ensure_aligned(src: 'RioRaster', ref: 'RioRaster', resampling="nearest") -> 'RioRaster':
            r = src
            # 1) Align CRS
            if r.get_crs() != ref.get_crs():
                r = r.reproject_to(ref.get_crs(), in_place=False, resampling=resampling)

            # 2) Align Extent/Grid (Padding/Clipping to match reference pixels exactly)
            # Note: Your pad_raster handles the float32 conversion and NaN filling internally
            padded = r.pad_raster(ref, in_place=False)
            return padded if padded is not None else r

        def _read_as_bands(r: 'RioRaster') -> np.ndarray:
            arr = r.get_data_array()
            if arr.ndim == 2:
                arr = arr[np.newaxis, ...]
            return arr

        if not sources:
            raise ValueError("No sources provided.")

        # --- LOGIC TO USE FIRST IMAGE AS REFERENCE ---
        if reference is not None:
            ref_r = reference
        else:
            # Take the first source. If it's an array, we must convert it to a
            # raster so we have access to metadata (or assume a default if purely arrays)
            first_item = sources[0]
            if isinstance(first_item, RioRaster):
                ref_r = first_item
            else:
                # If the very first item is an array and no reference is provided,
                # you may need a fallback or a specific error, as arrays have no CRS.
                # Here we assume it might be a numpy array you want to treat as the grid:
                raise ValueError("First source is a numpy array. Please provide a RioRaster "
                                 "reference or ensure the first source is a RioRaster.")

        # 1) Process all sources: Convert -> Align -> Read
        arrays = []
        for s in sources:
            r = _as_raster_like(ref_r, s)
            r = _ensure_aligned(r, ref_r, resampling=resampling)
            arrays.append(_read_as_bands(r))

        # 2) Force everything to float32 (NaN-safe stacking)
        arrays = [np.asarray(a, dtype=np.float32) for a in arrays]
        stacked = np.concatenate(arrays, axis=0)  # Shape: (Total_Bands, H, W)

        # 3) Build a clean metadata profile based on the reference
        meta = ref_r.get_meta().copy()

        # Calculate nodata value
        ref_nodata = ref_r.get_nodata_value()
        nodata = ref_nodata if ref_nodata is not None else np.nan

        meta.update({
            "count": stacked.shape[0],
            "dtype": "float32",
            "height": stacked.shape[1],
            "width": stacked.shape[2],
            "transform": ref_r.get_geo_transform(),
            "crs": ref_r.get_crs(),
            "nodata": nodata,
        })

        ds_reader = RioRaster.rio_dataset_from_array(stacked, meta, band_names or [])
        return RioRaster(ds_reader)



    @staticmethod
    def view_raster_on_folium(
        raster,
        tiles: str = "OpenStreetMap",
        gdf: GeoDataFrame = None,
        show_legend: bool = True,
        legend_title: str = "Raster Values",
        colormap="viridis",
        vmin=None,
        vmax=None,
        opacity: float = 0.7,
        output_html: str = None,
    ):
        """
        Display a single-band raster on an interactive Folium web map.

        Parameters
        ----------
        raster : RioRaster
            Raster object containing at least one band.
        tiles : str, optional (default="OpenStreetMap")
            Basemap tile provider used in the Folium map.

            Supported built-in tile names include:
                - "OpenStreetMap"                  → Standard OSM basemap
                - "Stamen Terrain"                 → Terrain / relief style
                - "Stamen Toner"                   → High-contrast B&W map
                - "Stamen Watercolor"              → Artistic watercolor map
                - "CartoDB positron"               → Clean light basemap
                - "CartoDB dark_matter"            → Dark background basemap
                - "Wikimedia"                      → Wikimedia OSM tiles

            You may also use **custom XYZ tile providers** using `folium.TileLayer`, e.g.:

            - Google Maps (roadmap)
              URL: "https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}"

            - Google Satellite
              URL: "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"

            - Esri World Imagery (satellite)
              URL: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

            - Esri Topographic
              URL: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"

            Notes
            -----
            • XYZ tile URLs must include placeholders: {x}, {y}, {z}.
            • Google and ESRI tiles may impose use restrictions.
            • Tile choice does not affect raster computation — only the visual background.

        gdf : GeoDataFrame, optional
            A vector boundary (single GeoDataFrame) to overlay on the map.
        show_legend : bool, default=True
            Whether to display a dynamic legend matching raster colormap.
        legend_title : str, optional
        colormap : str or callable, default="viridis"
            Name of matplotlib colormap.
        vmin, vmax : float, optional
            Color range limits. If None → computed from raster.
        opacity : float, default=0.7
            Opacity of raster overlay.
        output_html : str, optional
            If provided, the map is saved to an HTML file.

        Returns
        -------
        folium.Map
            Folium map object with raster overlay.

        Usage:
            r = RioRaster("tests/data/terrain/merit_dem.tif")
            aoi_gdf = your_aoi_gdf   # e.g. catchment boundary, villages, etc.

            m = RioProcess.view_raster_on_folium(
                raster=r,
                band=1,
                cmap="terrain",
                opacity=0.8,
                show_legend=True,
                legend_label="Elevation (m)",
                gdf=aoi_gdf,
                edgecolor="red",
                linewidth=1.0,
            )

            m.save("dem_with_aoi.html")

        """


        # ---------------------------------------------
        # Read raster data
        # ---------------------------------------------
        arr = raster.get_data_array(1).astype(float)
        nodata = raster.get_nodata_value()
        arr[arr == nodata] = np.nan

        vmin = np.nanmin(arr) if vmin is None else vmin
        vmax = np.nanmax(arr) if vmax is None else vmax

        cmap = cm.get_cmap(colormap)
        norm = colors.Normalize(vmin=vmin, vmax=vmax)

        rgba_img = cmap(norm(arr))
        rgba_img = (rgba_img * 255).astype("uint8")

        # encode PNG
        buf = io.BytesIO()
        plt_img = rasterio.plot.show
        import matplotlib.pyplot as plt

        plt.imsave(buf, rgba_img, format="png")
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode("utf-8")

        # bounding box
        transform = raster.get_geo_transform()
        h, w = arr.shape
        xmin = transform.c
        ymax = transform.f
        xmax = xmin + transform.a * w
        ymin = ymax + transform.e * h

        bounds = [[ymin, xmin], [ymax, xmax]]

        # ---------------------------------------------
        # Create Folium map centered on raster
        # ---------------------------------------------
        center_lat = (ymin + ymax) / 2
        center_lon = (xmin + xmax) / 2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles=tiles)

        # ---------------------------------------------
        # Add raster overlay
        # ---------------------------------------------
        folium.raster_layers.ImageOverlay(
            image="data:image/png;base64," + img_b64,
            bounds=bounds,
            opacity=opacity,
            name="Raster",
        ).add_to(m)

        # ---------------------------------------------
        # Add vector overlay if provided
        # ---------------------------------------------
        if gdf is not None and not gdf.empty:
            if gdf.crs != raster.get_crs():
                gdf = gdf.to_crs(raster.get_crs())

            folium.GeoJson(
                gdf,
                name="Vector Overlay",
                style_function=lambda x: {
                    "color": "green",
                    "weight": 2,
                    "fillOpacity": 0,
                },
            ).add_to(m)

        # ---------------------------------------------
        # Add legend
        # ---------------------------------------------
        if show_legend:
            gradient = "".join(
                [
                    f'<div style="background: rgb{tuple(int(c*255) for c in cmap(i/100)[:3])}; width: 100%; height: 3px"></div>'
                    for i in range(100)
                ]
            )

            legend_html = f"""
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: white;
                padding: 10px;
                border: 2px solid grey;
                z-index: 999999;
                font-size: 12px;
            ">
                <b>{legend_title}</b><br>
                {gradient}
                <div style="display:flex; justify-content:space-between;">
                    <span>{vmin:.2f}</span>
                    <span>{vmax:.2f}</span>
                </div>
            </div>
            """
            m.get_root().html.add_child(folium.Element(legend_html))

        folium.LayerControl().add_to(m)

        if output_html:
            m.save(output_html)

        return m

    @staticmethod
    def open_folium_in_browser(folium_map):
        """
        Open a Folium map in the default web browser without manually saving a file.
        Usage:
            m = RioProcess.view_raster_on_folium(raster)
            open_folium_in_browser(m)
        """
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        folium_map.save(tmp.name)
        webbrowser.open(tmp.name)


    @staticmethod
    def zonal_stats_by_band(
        raster: RioRaster,
        zones_gdf: gpd.GeoDataFrame,
        *,
        zone_id_field: str,
        stats: Sequence[str] = ("mean", "median", "std", "min", "max", "cv"),
        all_touched: bool = True,
        out_xlsx: Optional[str | Path] = None,
        sheet_name_prefix: str = "",
    ) -> Dict[str, pd.DataFrame]:
        """
        Compute zonal statistics and return band-wise DataFrames.

        Returns
        -------
        Dict[str, DataFrame]
            key   = band name
            value = zonal statistics dataframe for that band
        """

        ds = raster.get_dataset()
        if ds is None:
            raise ValueError("Raster dataset is not open.")

        gdf = zones_gdf.copy()
        if gdf.crs != ds.crs:
            gdf = gdf.to_crs(ds.crs)

        band_names = list(ds.descriptions)
        if not band_names or all(b is None for b in band_names):
            band_names = [f"band{i}" for i in range(1, ds.count + 1)]

        stat_set = set(stats)
        band_results: Dict[str, list] = {b: [] for b in band_names}

        def compute(arr: np.ndarray) -> dict:
            x = arr[np.isfinite(arr)]
            if x.size == 0:
                return {s: np.nan for s in stat_set}

            out = {}
            mu = np.mean(x)
            if "mean" in stat_set:
                out["mean"] = float(mu)
            if "median" in stat_set:
                out["median"] = float(np.median(x))
            if "min" in stat_set:
                out["min"] = float(np.min(x))
            if "max" in stat_set:
                out["max"] = float(np.max(x))
            if "std" in stat_set or "cv" in stat_set:
                std = float(np.std(x))
                if "std" in stat_set:
                    out["std"] = std
                if "cv" in stat_set:
                    out["cv"] = float(std / mu) if mu != 0 else np.nan
            return out

        for _, row in gdf.iterrows():
            geom = row.geometry
            zone_id = row[zone_id_field]

            out_img, _ = mask(
                ds,
                [geom],
                crop=True,
                all_touched=all_touched,
                nodata=ds.nodata,
                filled=True,
            )

            for i, band in enumerate(band_names):
                band_arr = out_img[i].astype("float32")
                if ds.nodata is not None:
                    band_arr[band_arr == ds.nodata] = np.nan

                stats_dict = compute(band_arr.ravel())
                stats_dict[zone_id_field] = zone_id
                band_results[band].append(stats_dict)

        # Convert to DataFrames
        band_dfs: Dict[str, pd.DataFrame] = {}
        for band, rows in band_results.items():
            df = pd.DataFrame(rows)
            cols = [zone_id_field] + [s for s in stats if s in df.columns]
            band_dfs[band] = df[cols]

        # Optional Excel export
        if out_xlsx:
            out_xlsx = Path(out_xlsx)
            out_xlsx.parent.mkdir(parents=True, exist_ok=True)

            with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
                for band, df in band_dfs.items():
                    sheet = f"{sheet_name_prefix}{band}"[:31]
                    df.to_excel(writer, sheet_name=sheet, index=False)

        return band_dfs


