import sys
from typing import Literal, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
import contextlib
import io
import tyro
import pycolmap
from loguru import logger
from hloc import extract_features, pairs_from_exhaustive, pairs_from_retrieval, match_features, reconstruction


@dataclass
class CLIArgs:
    """Arguments for the HLoc CLI"""

    images: Path  # Path to the images to process
    feature: Optional[str] = "superpoint_aachen"  # Feature extractor config to use
    matching_method: Optional[Literal["exhaustive", "sequential"]] = "exhaustive"  # Method for matching images
    top_k_matches: int = 50  # Number of top matches to use in sequential matching
    matcher: Optional[Literal["superglue", "superglue-fast",
                              "superpoint+lighglue"]] = "superglue"  # Feature matcher config to use
    matcher_weights: Literal["indoor", "outdoor"] = "outdoor"  # Weights for the matcher
    reconstruction: bool = True  # Run SfM reconstruction using COLMAP
    camera_model: Literal["SIMPLE_PINHOLE", "PINHOLE", "SIMPLE_RADIAL", "RADIAL", "OPENCV",
                          "FISHEYE"] = "OPENCV"  # Camera model to use
    single_camera: bool = True  # Use the same camera for all images
    global_bundle_adjustment: bool = True  # Perform global bundle adjustment
    refine_principal_point: bool = True  # Refine the principal point
    overwrite: bool = False  # Overwrite existing results
    progress: bool = False  # Show progress bar
    verbose: bool = False  # Show verbose output
    quiet: bool = False  # Suppress all output


def run(args: CLIArgs):
    contexts = []
    if not args.verbose or args.quiet:
        logging.disable(logging.CRITICAL)
        contexts.append(contextlib.redirect_stdout(io.StringIO()))
    if not args.progress or args.quiet:
        contexts.append(contextlib.redirect_stderr(io.StringIO()))

    logger.remove()
    if not args.quiet:
        logger.add(sys.stderr, level="DEBUG" if args.verbose else "INFO")

    hloc_dir = args.images.parent / "hloc"
    feature_path = hloc_dir / f"{args.feature}.h5"
    pairs_path = hloc_dir / "pairs.txt"
    matches_path = hloc_dir / "matches.h5"
    sfm_dir = args.images.parent / "sparse"

    image_list = [p.relative_to(args.images).as_posix() for p in args.images.iterdir()]

    with contextlib.ExitStack() as stack:
        for ctx in contexts:
            stack.enter_context(ctx)
        if args.feature:
            logger.info(f"Feature extraction: {args.feature}")
            extract_features.main(
                conf=extract_features.confs[args.feature],
                image_dir=args.images,
                export_dir=hloc_dir,
                image_list=image_list,
                feature_path=feature_path,
                overwrite=args.overwrite,
            )
        if args.matching_method:
            logger.info(f"Image pairing: {args.matching_method}")
            if args.matching_method == "exhaustive":
                pairs_from_exhaustive.main(
                    output=pairs_path,
                    image_list=image_list,
                    features=feature_path,
                )
            else:
                retrieval_path = extract_features.main(
                    conf=extract_features.confs["netvlad"],
                    image_dir=args.images,
                    export_dir=hloc_dir,
                    image_list=image_list,
                    feature_path=hloc_dir / "netvlad.h5",
                    overwrite=args.overwrite,
                )
                pairs_from_retrieval.main(
                    descriptors=retrieval_path,
                    output=pairs_path,
                    num_matched=min(len(image_list), args.top_k_matches),
                )
        if args.matcher:
            logger.info(f"Feature matching: {args.matcher}")
            matcher_conf = match_features.confs[args.matcher]
            if "weights" in matcher_conf["model"]:
                matcher_conf["model"]["weights"] = args.matcher_weights
            match_features.main(conf=matcher_conf,
                                pairs=pairs_path,
                                features=feature_path,
                                export_dir=hloc_dir,
                                matches=matches_path,
                                overwrite=args.overwrite)
        if args.reconstruction:
            image_options = pycolmap.ImageReaderOptions(camera_model=args.camera_model)
            camera_mode = pycolmap.CameraMode.PER_IMAGE
            if args.single_camera:
                camera_mode = pycolmap.CameraMode.SINGLE

            reconstruction.main(
                sfm_dir=sfm_dir,
                image_dir=args.images,
                pairs=pairs_path,
                features=feature_path,
                matches=matches_path,
                camera_mode=camera_mode,
                verbose=args.verbose,
                image_list=image_list,
                image_options=image_options,
            )

            if args.global_bundle_adjustment:
                rec = pycolmap.Reconstruction()
                rec.read(sfm_dir)
                options = pycolmap.BundleAdjustmentOptions(refine_principal_point=args.refine_principal_point)
                pycolmap.bundle_adjustment(rec, options)
                rec.write(sfm_dir)


def main():
    run(tyro.cli(CLIArgs))


if __name__ == "__main__":
    main()
