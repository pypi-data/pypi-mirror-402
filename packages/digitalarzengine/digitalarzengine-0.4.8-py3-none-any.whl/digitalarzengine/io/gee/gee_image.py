import json
import os
import shutil
import time
import traceback
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, Sequence

import ee
import pandas as pd
import requests
from tqdm import tqdm

from digitalarzengine.io.file_io import FileIO
from digitalarzengine.io.gee.gee_region import GEERegion
from digitalarzengine.processing.raster.rio_process import RioProcess


@dataclass
class DownloadResult:
    ok: bool
    error: Optional[str] = None
    tiles_downloaded: int = 0
    tiles_skipped: int = 0
    output_path: Optional[str] = None
    metadata_path: Optional[str] = None


class GEEImage:
    """
    Convenience wrapper around ee.Image for:
    - bands / scale / metadata helpers
    - generating download URLs
    - tiled download + mosaic to GeoTIFF
    """

    def __init__(self, img: ee.Image, logger: Optional[logging.Logger] = None):
        self.image: ee.Image = img
        self.bands: Optional[List[str]] = None
        self.log = logger or logging.getLogger(self.__class__.__name__)

    # ----------------------------
    # Basic helpers
    # ----------------------------
    def get_image_bands(self) -> List[str]:
        try:
            return self.image.bandNames().getInfo()
        except ee.EEException as e:
            self.log.exception("Failed to get band names from ee.Image: %s", e)
            return []

    def get_image_date(self) -> datetime:
        """
        Returns system:time_start as a python datetime (UTC).
        """
        latest_date = ee.Date(self.image.get("system:time_start")).getInfo()
        formatted = datetime.utcfromtimestamp(latest_date["value"] / 1000)
        self.log.info("Latest acquisition date: %s", formatted.strftime("%Y-%m-%d"))
        return formatted

    def get_scale(self, b_name: Optional[str] = None) -> Union[float, Dict[str, float]]:
        """
        Get nominal scale(s) in meters.
        - If b_name is None: returns {band_name: scale}
        - Else returns scale for that band
        """
        if b_name is None:
            band_names = self.image.bandNames().getInfo()
            res: Dict[str, float] = {}
            for bn in band_names:
                s = self.image.select(bn).projection().nominalScale().getInfo()
                res[bn] = float(s)
            return res
        else:
            s = self.image.select(b_name).projection().nominalScale().getInfo()
            return float(s)

    def get_image_metadata(self) -> Dict[str, Any]:
        return self.image.getInfo()

    # ----------------------------
    # URL + download helpers
    # ----------------------------
    def get_image_url(
        self,
        img_name: str,
        aoi: ee.Geometry,
        scale: Optional[float] = None,
        bands: Optional[List[str]] = None,
        fmt: str = "GEO_TIFF",
    ) -> Optional[str]:
        """
        Generates an EE download URL for the (possibly clipped) image.

        Notes:
        - Passing 'bands' is optional. If omitted, EE will export all bands.
        - 'aoi' should be an ee.Geometry (Polygon/Rectangle/etc).
        """
        try:
            if bands is None:
                if self.bands is None:
                    self.bands = self.get_image_bands()
                bands = self.bands

            params: Dict[str, Any] = {
                "name": img_name,
                "region": aoi,
                "format": fmt,
            }
            if scale is not None:
                params["scale"] = scale

            # If you want to export only certain bands, include them.
            # If you want all bands, you may omit "bands" entirely.
            if bands:
                params["bands"] = bands

            # EE Python API typically supports calling getDownloadURL directly on the image.
            return self.image.getDownloadURL(params)

        except ee.EEException as e:
            self.log.exception("Earth Engine error while creating download URL: %s", e)
            return None
        except Exception as e:
            self.log.exception("Unexpected error while creating download URL: %s", e)
            return None

    @staticmethod
    def download_from_url(
        url: str,
        file_path: str,
        allow_redirects: bool = True,
        timeout: int = 180,
        retries: int = 3,
        backoff: float = 1.6,
        session: Optional[requests.Session] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Download bytes from URL to file_path with retry and useful error reporting.
        Returns (ok, error_message).
        """
        sess = session or requests.Session()
        last_err: Optional[str] = None

        for attempt in range(1, retries + 1):
            try:
                r = sess.get(url, allow_redirects=allow_redirects, timeout=timeout)
                if r.status_code == 200:
                    FileIO.mkdirs(file_path)
                    with open(file_path, "wb") as f:
                        f.write(r.content)
                    return True, None

                # Try parse JSON error else fallback to text
                try:
                    last_err = json.dumps(r.json())[:1500]
                except Exception:
                    last_err = (r.text or "").strip()[:1500]

            except Exception as e:
                last_err = str(e)[:1500]

            if attempt < retries:
                time.sleep(backoff ** attempt)

        return False, last_err

    # ----------------------------
    # Main workflow: tiled download + mosaic
    # ----------------------------
    def download_image(
        self,
        file_path: str,
        img_region: GEERegion,
        scale: float = -1,
        bit_depth: int = 16,
        no_of_bands: Optional[int] = None,
        delete_folder: bool = True,
        within_aoi_only: bool = False,
        save_metadata: bool = True,
        meta_data: Optional[Dict[str, Any]] = None,
        bands: Optional[List[str]] = None,
        retries: int = 3,
        timeout: int = 180,
        lookup_table: Optional[pd.DataFrame] = None,
    ) -> DownloadResult:
        """
        Downloads the image over a (tiled) GEERegion and mosaics into a single GeoTIFF.

        Args:
            file_path: output GeoTIFF path.
            img_region: GEERegion that yields tiles via get_tiles().
            scale: meters. If -1, uses min band scale.
            bit_depth: passed to tiler.
            no_of_bands: optional. If None, derived from bands.
            delete_folder: deletes temp tiles folder after success/failure.
            within_aoi_only: passed to tiler.
            save_metadata: saves *_meta_data.json alongside file_path.
            meta_data: if provided, used instead of self.image.getInfo()
            bands: optional list of band names to export.
            retries/timeout: HTTP download behavior.
            lookup_table: optional pd.DataFrame with colums, pixel_values , colors , class_names
        Returns:
            DownloadResult with ok/error and some bookkeeping.
        """
        result = DownloadResult(ok=False, output_path=file_path)

        # Derive scale
        if scale == -1:
            sc = self.get_scale()
            if isinstance(sc, dict) and sc:
                scale = float(min(sc.values()))
            else:
                scale = float(sc) if isinstance(sc, (int, float)) else 10.0  # fallback

        # Determine bands
        if bands is not None:
            self.bands = bands
        elif self.bands is None:
            self.bands = self.get_image_bands()

        if no_of_bands is None:
            no_of_bands = len(self.bands or [])

        # Metadata
        if meta_data is None:
            meta_data = self.get_image_metadata()

        # Save metadata
        metadata_fp: Optional[str] = None
        if save_metadata:
            try:
                metadata_fp = f"{file_path[:-4]}_meta_data.json"
                FileIO.mkdirs(metadata_fp)
                with open(metadata_fp, "w", encoding="utf-8") as f:
                    json.dump(meta_data, f, ensure_ascii=False, indent=2)
                result.metadata_path = metadata_fp
            except Exception as e:
                # Non-fatal: keep going, but record error
                self.log.warning("Failed saving metadata: %s", e)

        # Band IDs for output naming (prefer actual selected bands)
        band_ids: List[str] = list(self.bands or [])
        # If bands missing, attempt fallback to metadata
        if not band_ids:
            try:
                band_ids = [b["id"] for b in meta_data.get("bands", []) if "id" in b]
            except Exception:
                band_ids = []

        # Prepare temp tile folder
        dir_name = os.path.dirname(file_path)
        img_name, _ = os.path.splitext(os.path.basename(file_path))
        download_dir_name = os.path.join(dir_name, img_name)
        FileIO.mkdirs(download_dir_name)

        # Build tile list first (so tqdm has total)
        required_tiles: List[Tuple[Any, Any]] = []
        try:
            for tile_region, index in img_region.get_tiles(
                no_of_bands, scale, bit_depth=bit_depth, within_aoi_only=within_aoi_only
            ):
                required_tiles.append((tile_region, index))
        except Exception as e:
            result.error = f"Failed to generate tiles: {e}"
            if delete_folder and os.path.exists(download_dir_name):
                shutil.rmtree(download_dir_name, ignore_errors=True)
            return result

        sess = requests.Session()
        tiles_downloaded = 0
        tiles_skipped = 0

        self.log.info("Downloading %d tiles into %s", len(required_tiles), download_dir_name)

        progress_bar = tqdm(desc="Downloading Tiles", unit="tile", total=len(required_tiles))
        for tile_region, index in required_tiles:
            temp_file_path = os.path.join(
                download_dir_name, f"r{index[0]}c{index[1]}.tif"
            )

            if os.path.exists(temp_file_path):
                tiles_skipped += 1
                progress_bar.update(1)
                continue

            aoi = tile_region.get_aoi()
            url = self.get_image_url(img_name=img_name, aoi=aoi, scale=scale, bands=self.bands)

            if url is None:
                # keep going; mosaic may still fail later if tiles missing
                tiles_skipped += 1
                progress_bar.update(1)
                continue

            ok, err = self.download_from_url(
                url=url,
                file_path=temp_file_path,
                timeout=timeout,
                retries=retries,
                session=sess,
            )
            if ok:
                tiles_downloaded += 1
            else:
                tiles_skipped += 1
                self.log.warning("Tile download failed (%s): %s", temp_file_path, err)

            progress_bar.update(1)
        progress_bar.close()

        result.tiles_downloaded = tiles_downloaded
        result.tiles_skipped = tiles_skipped

        # Mosaic + save + cleanup
        try:
            raster = RioProcess.mosaic_images(download_dir_name)
            if lookup_table is not None:
                raster.save_with_colormap_and_lookup_table(file_path, lookup_table,band_names=band_ids or None)
            else:
                raster.save_to_file(file_path, band_names=band_ids or None)
            self.log.info("Image downloaded: %s", file_path)
            result.ok = True
            return result

        except Exception as e:
            traceback.print_exc()
            result.error = f"Mosaic/save failed: {e}"
            result.ok = False
            return result

        finally:
            if delete_folder and os.path.exists(download_dir_name):
                shutil.rmtree(download_dir_name, ignore_errors=True)

    # ----------------------------
    # Stats helper
    # ----------------------------
    @staticmethod
    def get_band_stats(dataset: ee.Image, region: ee.Geometry, scale: float) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves min, max, mean, std dev for each band using a combined reducer (single reduceRegion).
        """
        reducer = (
            ee.Reducer.minMax()
            .combine(ee.Reducer.mean(), sharedInputs=True)
            .combine(ee.Reducer.stdDev(), sharedInputs=True)
        )

        result = dataset.reduceRegion(
            reducer=reducer,
            geometry=region,
            scale=scale,
            maxPixels=1e13,
        )

        band_names = dataset.bandNames().getInfo()
        out: Dict[str, Dict[str, Any]] = {}

        for b in band_names:
            out[b] = {
                "min": result.get(f"{b}_min").getInfo(),
                "max": result.get(f"{b}_max").getInfo(),
                "mean": result.get(b).getInfo(),
                "std": result.get(f"{b}_stdDev").getInfo(),
            }
        return out


    @staticmethod
    def stack_images_as_bands(
        images: Sequence[ee.Image],
        band_names: Sequence[Union[int, str]],
        band: Optional[str] = None,
        band_index: int = 0,
        clean_collection_prefix: bool = True,
    ) -> ee.Image:
        """
        Stack images into a single multiband ee.Image with custom band names.

        Args:
            images: sequence of ee.Image (one per band)
            band_names: band names to assign (years, months, labels, etc.)
            band: optional band name to select from each image
            band_index: band index fallback if image is multi-band
            clean_collection_prefix: removes '0_', '1_' prefixes from toBands()

        Returns:
            ee.Image with bands named exactly as band_names
        """
        if len(images) != len(band_names):
            raise ValueError("images and band_names must have the same length")

        def prep(img, name):
            img = ee.Image(img)
            if band is not None:
                img = img.select([band])
            else:
                img = img.select([band_index])

            return img.rename([ee.String(name)])

        ee_imgs: List[ee.Image] = [
            prep(images[i], str(band_names[i]))
            for i in range(len(images))
        ]

        stacked = ee.ImageCollection(ee_imgs).toBands()

        if clean_collection_prefix:
            old_names = stacked.bandNames()
            new_names = old_names.map(
                lambda s: ee.String(s).split("_").get(-1)
            )
            stacked = stacked.rename(new_names)

        return stacked
