import os
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, Union

import ee
from geopandas import GeoDataFrame

from digitalarzengine.io.gee.gee_image import GEEImage
from digitalarzengine.io.gee.gee_image_collection import CollectionOp, GEEImageCollection
from digitalarzengine.pipeline.gee_pipeline import GEEPipeline


class SoilCapacityAnalysis:
    """
    Soil water availability workflow for AEZ / MRDA using OpenLandMap soil layers.
    https://developers.google.com/earth-engine/datasets/catalog/OpenLandMap_SOL_SOL_CLAY-WFRACTION_USDA-3A1A1A_M_v02
    Produces (consistent, AEZ-friendly outputs):
      1) Field Capacity (FC) as volumetric fraction (m3/m3) per OpenLandMap depth band
      2) Wilting Point (WP) as volumetric fraction (m3/m3) per OpenLandMap depth band
      3) Soil Capacity / Plant Available Water fraction (FC - WP) per depth band,
         with optional total fraction band
      4) Thickness-weighted water depths in *cm* for:
           - FC per layer + optional total band
           - WP per layer + optional total band
           - AWC per layer (FC-WP) + optional total band
    """

    def __init__(self, gee_pipline: Optional[GEEPipeline], aoi_gdv: GeoDataFrame, soil_data_dir: str):
        self.aoi_gdv = aoi_gdv
        self.gee_pipeline: Optional[GEEPipeline] = gee_pipline

        # OpenLandMap band labels (depth markers in cm)
        self.olm_depths = [0, 10, 30, 60, 100, 200]
        self.olm_bands = [f"b{d}" for d in self.olm_depths]
        # Export scale (OpenLandMap native is ~250m)
        self.scale = 250
        self.soil_data_dir = soil_data_dir

        # Layer thickness in *cm* for depth intervals up to 200 cm:
        # 0–10, 10–30, 30–60, 60–100, 100–200
        # self.thickness_cm_by_band: Dict[str, int] = {
        #     "b0": 10,
        #     "b10": 20,
        #     "b30": 30,
        #     "b60": 40,
        #     "b100": 100,
        # }
        thicknesses = [
            self.olm_depths[i + 1] - self.olm_depths[i]
            for i in range(len(self.olm_depths) - 1)
        ]

        self.thickness_cm_by_band: Dict[str, int] = dict(
            zip(self.olm_bands, thicknesses)
        )

    # ---------------------------------------------------------------------
    # DATA SOURCES (OpenLandMap)
    # ---------------------------------------------------------------------
    @staticmethod
    def get_band_title(
            band_name: Literal["b0", "b10", "b30", "b60", "b100"]
    ) -> str:
        band_titles = {
            "b0": "0–10 cm",
            "b10": "10–30 cm",
            "b30": "30–60 cm",
            "b60": "60–100 cm",
            "b100": "100–200 cm",
        }
        return band_titles[band_name]


    def get_band_thickness(self, band_name: Literal["b0", "b10", "b30", "b60", "b100"]) -> int:
        return self.thickness_cm_by_band[band_name]

    @staticmethod
    def get_soil_prop(param: str) -> ee.Image:
        """
        Fetch OpenLandMap soil property as an ee.Image and apply dataset scaling.

        sand, clay: percent -> fraction via 0.01
        orgc: dataset scaling -> kg/kg via 5*0.001 (as used in your codebase)
        """
        if param == "sand":
            snippet = "OpenLandMap/SOL/SOL_SAND-WFRACTION_USDA-3A1A1A_M/v02"
            scale_factor = 0.01
        elif param == "clay":
            snippet = "OpenLandMap/SOL/SOL_CLAY-WFRACTION_USDA-3A1A1A_M/v02"
            scale_factor = 0.01
        elif param == "orgc":
            snippet = "OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02"
            scale_factor = 5 * 0.001
        else:
            raise ValueError(f"Unknown param: {param}")

        return ee.Image(snippet).multiply(scale_factor)

    def get_soil_data(self) -> Tuple[ee.Image, ee.Image, ee.Image, ee.Image]:
        """
        Load base soil property rasters for the AOI.

        Returns
        -------
        sand : ee.Image
            Sand fraction per depth band.
        clay : ee.Image
            Clay fraction per depth band.
        orgc : ee.Image
            Organic carbon (scaled) per depth band.
        orgm : ee.Image
            Organic matter estimate using Van Bemmelen factor: OM = 1.724 * orgc
        """
        if self.gee_pipeline is None:
            self.gee_pipeline = GEEPipeline(self.aoi_gdv)

        sand = self.get_soil_prop("sand")
        clay = self.get_soil_prop("clay")
        orgc = self.get_soil_prop("orgc")

        # OM = 1.724 * orgc (Van Bemmelen factor)
        orgm = orgc.multiply(1.724)
        return sand, clay, orgc, orgm

    # ---------------------------------------------------------------------
    # PATHS (consistent filenames + units)
    # ---------------------------------------------------------------------
    @staticmethod
    def get_raster_path(
        soil_data_dir: str,
        param: Literal[
            "field_capacity_frac",
            "wilting_point_frac",
            "soil_capacity_frac",
            "fc_layers_cm",
            "wp_layers_cm",
            "awc_layers_cm",
        ],
    ) -> str:
        """
        Centralized output naming for MRDA/AEZ products.
        """
        os.makedirs(soil_data_dir, exist_ok=True)
        mapping = {
            # volumetric fraction rasters (m3/m3)
            "field_capacity_frac": os.path.join(soil_data_dir, "field_capacity_frac.tif"),
            "wilting_point_frac": os.path.join(soil_data_dir, "wilting_point_frac.tif"),
            "soil_capacity_frac": os.path.join(soil_data_dir, "soil_capacity_frac.tif"),

            # thickness-weighted layer water depths in cm (cm water over layer)
            "fc_layers_cm": os.path.join(soil_data_dir, "fc_layers_cm.tif"),
            "wp_layers_cm": os.path.join(soil_data_dir, "wp_layers_cm.tif"),
            "awc_layers_cm": os.path.join(soil_data_dir, "awc_layers_cm.tif"),
        }
        if param not in mapping:
            raise ValueError(f"Unknown param: {param}")
        return mapping[param]

    @staticmethod
    def get_band_name(depth: Union[int, str]) -> str:
        """
        Accepts 30 or "b30" and returns "b30".
        """
        olm_depths = [0, 10, 30, 60, 100, 200]
        olm_bands = [f"b{d}" for d in olm_depths]
        band = f"b{depth}" if isinstance(depth, int) else depth
        if band not in olm_bands:
            raise ValueError(f"depth/band {depth} doesn't exist. Choose from {olm_bands}")
        return band

    # ---------------------------------------------------------------------
    # CORE: FC and WP as volumetric fractions (m3/m3)
    # ---------------------------------------------------------------------
    def calculate_field_capacity_and_wilting_point(
        self,
        export_multiband: bool = True,
        export_per_depth: bool = False,
    ) -> Tuple[ee.Image, ee.Image]:
        """
        Compute Field Capacity (FC; theta33) and Wilting Point (WP; theta1500)
        as volumetric fractions (m3/m3), for each OpenLandMap depth band.

        Output bands: b0, b10, b30, b60, b100, b200

        Notes
        -----
        - Fix applied: WP band is added only once per depth band.
        - Exports (optional):
            - multiband FC/WP fraction rasters
            - per-band single rasters
        """
        if self.gee_pipeline is None:
            self.gee_pipeline = GEEPipeline(self.aoi_gdv)

        # Dummy init to enable addBands in loop
        wilting_point = ee.Image.constant(0).rename("dummy")
        field_capacity = ee.Image.constant(0).rename("dummy")

        sand, clay, orgc, orgm = self.get_soil_data()

        for key in self.olm_bands:
            si = sand.select(key)
            ci = clay.select(key)
            oi = orgm.select(key)

            # --- Wilting Point (theta1500) ---
            theta_1500ti = ee.Image(0).expression(
                "-0.024 * S + 0.487 * C + 0.006 * OM + 0.005 * (S * OM) "
                "- 0.013 * (C * OM) + 0.068 * (S * C) + 0.031",
                {"S": si, "C": ci, "OM": oi},
            )

            wpi = theta_1500ti.expression(
                "T1500 + (0.14 * T1500 - 0.002)",
                {"T1500": theta_1500ti},
            ).rename(key).float()

            # Add WP once (bug fix vs earlier duplicate add)
            wilting_point = wilting_point.addBands(wpi)

            # --- Field Capacity (theta33) ---
            theta_33ti = ee.Image(0).expression(
                "-0.251 * S + 0.195 * C + 0.011 * OM + 0.006 * (S * OM) "
                "- 0.027 * (C * OM) + 0.452 * (S * C) + 0.299",
                {"S": si, "C": ci, "OM": oi},
            )

            fci = theta_33ti.expression(
                "T33 + (1.283 * T33 * T33 - 0.374 * T33 - 0.015)",
                {"T33": theta_33ti},
            ).rename(key).float()

            field_capacity = field_capacity.addBands(fci)

        # Select only real bands
        wilting_point = wilting_point.select(self.olm_bands)
        field_capacity = field_capacity.select(self.olm_bands)

        # Export multiband rasters (fractions)
        if export_multiband:
            fc_fp = self.get_raster_path(self.soil_data_dir, "field_capacity_frac")
            wp_fp = self.get_raster_path(self.soil_data_dir, "wilting_point_frac")

            if not os.path.exists(fc_fp):
                GEEImage(field_capacity).download_image(
                    fc_fp, self.gee_pipeline.region, self.scale, save_metadata=False
                )
            if not os.path.exists(wp_fp):
                GEEImage(wilting_point).download_image(
                    wp_fp, self.gee_pipeline.region, self.scale, save_metadata=False
                )

        # Optional export per depth (fractions)
        if export_per_depth:
            for b in self.olm_bands:
                fc_b_fp = os.path.join(self.soil_data_dir, f"field_capacity_frac_{b}.tif")
                wp_b_fp = os.path.join(self.soil_data_dir, f"wilting_point_frac_{b}.tif")
                if not os.path.exists(fc_b_fp):
                    GEEImage(field_capacity.select(b)).download_image(
                        fc_b_fp, self.gee_pipeline.region, self.scale, save_metadata=False
                    )
                if not os.path.exists(wp_b_fp):
                    GEEImage(wilting_point.select(b)).download_image(
                        wp_b_fp, self.gee_pipeline.region, self.scale, save_metadata=False
                    )

        return field_capacity, wilting_point

    # ---------------------------------------------------------------------
    # SOIL CAPACITY FRACTION (FC - WP) per depth + optional total band
    # ---------------------------------------------------------------------
    def calculate_soil_capacity_per_depth(
        self,
        include_total_band: bool = True,
        include_b200_in_total: bool = False,
        export: bool = True,
    ) -> ee.Image:
        """
        Compute soil capacity (plant-available water fraction) per depth:
            soil_capacity_frac = FC - WP

        Output:
            - Bands: b0, b10, b30, b60, b100, b200 (fractions)
            - Optional: total_soil_capacity_frac = sum of selected depth bands

        Notes
        -----
        - Volumetric fraction is unitless (m3/m3).
        - Total sum excludes b200 by default to avoid possible double-counting.
        """
        if self.gee_pipeline is None:
            self.gee_pipeline = GEEPipeline(self.aoi_gdv)

        fc_frac, wp_frac = self.calculate_field_capacity_and_wilting_point(
            export_multiband=False, export_per_depth=False
        )

        soil_capacity_frac = fc_frac.subtract(wp_frac).select(self.olm_bands)

        if include_total_band:
            # Default: sum layered bands b0..b100 (depth intervals)
            sum_bands = ["b0", "b10", "b30", "b60", "b100"]
            if include_b200_in_total:
                sum_bands = sum_bands + ["b200"]

            total_frac = (
                soil_capacity_frac.select(sum_bands)
                .reduce(ee.Reducer.sum())
                .rename("total_soil_capacity_frac")
                .float()
            )

            soil_capacity_frac = soil_capacity_frac.addBands(total_frac)

        if export:
            out_fp = self.get_raster_path(self.soil_data_dir, "soil_capacity_frac")
            if not os.path.exists(out_fp):
                GEEImage(soil_capacity_frac).download_image(
                    out_fp, self.gee_pipeline.region, self.scale, save_metadata=False
                )

        return soil_capacity_frac

    # ---------------------------------------------------------------------
    # INTERNAL: Convert fraction image -> layer water depth in cm (+ total)
    # ---------------------------------------------------------------------
    def _layers_cm_from_fraction(
        self,
        frac_img: ee.Image,
        *,
        include_100_200: bool,
        band_prefix: str,
        include_total_band: bool,
        total_name: str,
    ) -> List[ee.Image]:
        """
        Convert a volumetric fraction image (FC or WP or PAW) into water depth per layer (cm):

            layer_water_cm = fraction * layer_thickness_cm

        This yields "cm of water" potentially stored in that layer.
        """
        # Candidate layers up to 100 cm
        candidate_bands = ["b0", "b10", "b30", "b60"]

        # Optionally include 100–200 cm
        if include_100_200:
            candidate_bands.append("b100")

        layers: List[ee.Image] = []
        total = ee.Image(0)

        for b in candidate_bands:
            layer_cm = (
                frac_img.select(b)
                .multiply(self.thickness_cm_by_band[b])
                .rename(f"{band_prefix}_{b}_cm")
                .float()
            )
            layers.append(layer_cm)
            total = total.add(layer_cm)

        if include_total_band:
            layers.append(total.rename(total_name).float())

        return layers

    # ---------------------------------------------------------------------
    # FC per layer in cm (+ optional total band)
    # ---------------------------------------------------------------------
    def calculate_fc_cm_per_layer(
        self,
        include_100_200: bool = True,
        include_total_band: bool = True,
        export: bool = True,
    ) -> List[ee.Image]:
        """
        Field Capacity water storage per layer (cm water):
            FC_layer(cm) = FC_fraction * thickness_cm
        """
        if self.gee_pipeline is None:
            self.gee_pipeline = GEEPipeline(self.aoi_gdv)

        fc_frac, wp_frac = self.calculate_field_capacity_and_wilting_point(
            export_multiband=False, export_per_depth=False
        )

        layers = self._layers_cm_from_fraction(
            fc_frac,
            include_100_200=include_100_200,
            band_prefix="fc",
            include_total_band=include_total_band,
            total_name=("fc_total_0_200_cm" if include_100_200 else "fc_total_0_100_cm"),
        )

        if export:
            out_fp = self.get_raster_path(self.soil_data_dir, "fc_layers_cm")
            if not os.path.exists(out_fp):
                img_coll = GEEImageCollection.from_images(layers)
                gee_img = GEEImageCollection.to_gee_img(img_coll, op=CollectionOp.TO_BANDS)
                GEEImage(gee_img).download_image(
                    out_fp, self.gee_pipeline.region, self.scale, save_metadata=False
                )

        return layers

    # ---------------------------------------------------------------------
    # WP per layer in cm (+ optional total band)
    # ---------------------------------------------------------------------
    def calculate_wp_cm_per_layer(
        self,
        include_100_200: bool = True,
        include_total_band: bool = True,
        export: bool = True,
    ) -> List[ee.Image]:
        """
        Wilting Point water storage per layer (cm water):
            WP_layer(cm) = WP_fraction * thickness_cm
        """
        if self.gee_pipeline is None:
            self.gee_pipeline = GEEPipeline(self.aoi_gdv)

        fc_frac, wp_frac = self.calculate_field_capacity_and_wilting_point(
            export_multiband=False, export_per_depth=False
        )

        layers = self._layers_cm_from_fraction(
            wp_frac,
            include_100_200=include_100_200,
            band_prefix="wp",
            include_total_band=include_total_band,
            total_name=("wp_total_0_200_cm" if include_100_200 else "wp_total_0_100_cm"),
        )

        if export:
            out_fp = self.get_raster_path(self.soil_data_dir, "wp_layers_cm")
            if not os.path.exists(out_fp):
                img_coll = GEEImageCollection.from_images(layers)
                gee_img = GEEImageCollection.to_gee_img(img_coll, op=CollectionOp.TO_BANDS)
                GEEImage(gee_img).download_image(
                    out_fp, self.gee_pipeline.region, self.scale, save_metadata=False
                )

        return layers

    # ---------------------------------------------------------------------
    # AWC per layer in cm (+ optional total band)
    # ---------------------------------------------------------------------
    def calculate_awc_cm_per_layer(
        self,
        include_100_200: bool = True,
        include_total_band: bool = True,
        export: bool = True,
    ) -> List[ee.Image]:
        """
        Available Water Capacity per layer (cm water):
            AWC_layer(cm) = (FC_fraction - WP_fraction) * thickness_cm
        """
        if self.gee_pipeline is None:
            self.gee_pipeline = GEEPipeline(self.aoi_gdv)

        fc_frac, wp_frac = self.calculate_field_capacity_and_wilting_point(
            export_multiband=False, export_per_depth=False
        )

        paw_frac = fc_frac.subtract(wp_frac)

        layers = self._layers_cm_from_fraction(
            paw_frac,
            include_100_200=include_100_200,
            band_prefix="awc",
            include_total_band=include_total_band,
            total_name=("awc_total_0_200_cm" if include_100_200 else "awc_total_0_100_cm"),
        )

        if export:
            out_fp = self.get_raster_path(self.soil_data_dir, "awc_layers_cm")
            if not os.path.exists(out_fp):
                img_coll = GEEImageCollection.from_images(layers)
                gee_img = GEEImageCollection.to_gee_img(img_coll, op=CollectionOp.TO_BANDS)
                GEEImage(gee_img).download_image(
                    out_fp, self.gee_pipeline.region, self.scale, save_metadata=False
                )

        return layers


if __name__ == "__main__":
    """
    Example execution script for SoilCapacityAnalysis.

    This script demonstrates:
      - AOI initialization
      - GEE pipeline setup
      - Generation of soil water capacity products required for AEZ analysis

    Outputs produced (in cm units where applicable):
      - Field Capacity fraction per depth
      - Wilting Point fraction per depth
      - Soil Capacity (FC − WP) fraction per depth + total
      - FC, WP, and AWC per layer in cm + total bands
    """
    aoi_gdf = GeoDataFrame() # any geodataframe

    print("AOI loaded. Bounds:", aoi_gdf.total_bounds.tolist())

    # ------------------------------------------------------------------
    # 2. Initialize GEE pipeline
    # ------------------------------------------------------------------
    gee_pipeline = None   #init_gee_pipeline(aoi_gdf)

    # ------------------------------------------------------------------
    # 3. Output directory
    # ------------------------------------------------------------------
    # from app.agri_bussiness.analysis.land_cover_analysis import OUTPUT_DIR
    #
    # soil_data_dir = OUTPUT_DIR / "soil_data"
    # soil_data_dir.mkdir(parents=True, exist_ok=True)
    soil_data_dir = Path("/Users/juan/Downloads/soil_data")

    # ------------------------------------------------------------------
    # 4. Initialize SoilCapacityAnalysis
    # ------------------------------------------------------------------
    soil_analysis = SoilCapacityAnalysis(
        gee_pipline=gee_pipeline,
        aoi_gdv=aoi_gdf,
        soil_data_dir=str(soil_data_dir),
    )

    # ------------------------------------------------------------------
    # 5. Compute volumetric soil moisture fractions
    # ------------------------------------------------------------------
    print("Computing Field Capacity and Wilting Point (fractions)...")
    fc_frac, wp_frac = soil_analysis.calculate_field_capacity_and_wilting_point(
        export_multiband=True,
        export_per_depth=False,
    )

    print("FC bands:", fc_frac.bandNames().getInfo())
    print("WP bands:", wp_frac.bandNames().getInfo())

    # ------------------------------------------------------------------
    # 6. Compute soil capacity fraction per depth + total band
    # ------------------------------------------------------------------
    print("Computing soil capacity fraction (FC − WP) per depth...")
    soil_capacity_frac = soil_analysis.calculate_soil_capacity_per_depth(
        include_total_band=True,
        include_b200_in_total=False,
        export=True,
    )

    print("Soil capacity bands:", soil_capacity_frac.bandNames().getInfo())

    # ------------------------------------------------------------------
    # 7. Compute Field Capacity per layer in cm
    # ------------------------------------------------------------------
    print("Computing Field Capacity per layer (cm)...")
    soil_analysis.calculate_fc_cm_per_layer(
        include_100_200=True,
        include_total_band=True,
        export=True,
    )

    # ------------------------------------------------------------------
    # 8. Compute Wilting Point per layer in cm
    # ------------------------------------------------------------------
    print("Computing Wilting Point per layer (cm)...")
    soil_analysis.calculate_wp_cm_per_layer(
        include_100_200=True,
        include_total_band=True,
        export=True,
    )

    # ------------------------------------------------------------------
    # 9. Compute Available Water Capacity (AWC) per layer in cm
    #    (This directly supports Tables 1–6)
    # ------------------------------------------------------------------
    print("Computing Available Water Capacity (AWC) per layer (cm)...")
    awc_layers = soil_analysis.calculate_awc_cm_per_layer(
        include_100_200=True,
        include_total_band=True,
        export=True,
    )

    print("AWC bands exported:")
    for img in awc_layers:
        print(" -", img.bandNames().getInfo())

    print("\nSoil water capacity processing completed successfully.")
