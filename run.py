import sys
from typing import Literal, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
import contextlib
import io
from multiprocessing import cpu_count
import tyro
import pycolmap
from loguru import logger
from hloc import (
    extract_features,
    pairs_from_exhaustive,
    pairs_from_retrieval,
    match_features,
    reconstruction,
)


@dataclass
class CLIArgs:
    """Arguments for the HLoc CLI"""

    images: Path  # Path to the images to process
    feature: Optional[
        Literal[
            "superpoint_aachen",
            "superpoint_max",
            "superpoint_inloc",
            "r2d2",
            "d2net-ss",
            "sift",
            "sosnet",
            "disk",
            "aliked-n16",
        ]
    ] = "superpoint_aachen"  # Feature extractor config to use
    pairs: Optional[Literal["exhaustive", "retrieval"]] = (
        "retrieval"  # Pairing method to use
    )
    retrieval: Literal["dir", "netvlad", "openlib", "eigenplaces"] = (
        "netvlad"  # Feature extractor config to use for retrieval
    )
    top_k_matches: int = 50  # Number of top matches to use in pairing from retrieval
    matcher: Optional[
        Literal[
            "superpoint+lightglue",
            "disk+lightglue",
            "aliked+lightglue",
            "superglue",
            "superglue-fast",
            "NN-superpoint",
            "NN-ratio",
            "NN-mutual",
            "adalam",
        ]
    ] = "superglue"  # Feature matcher config to use
    matcher_weights: Literal["indoor", "outdoor"] = "outdoor"  # Weights for the matcher
    reconstruction: bool = True  # Run SfM reconstruction using COLMAP
    camera_model: Literal[
        "SIMPLE_PINHOLE", "PINHOLE", "SIMPLE_RADIAL", "RADIAL", "OPENCV", "FISHEYE"
    ] = "OPENCV"  # Camera model to use
    single_camera: bool = True  # Use the same camera for all images
    global_bundle_adjustment: bool = True  # Perform global bundle adjustment
    refine_principal_point: bool = True  # Refine the principal point
    overwrite: bool = False  # Overwrite existing results
    progress: bool = False  # Show progress bar
    verbose: bool = False  # Show verbose output
    quiet: bool = False  # Suppress all output
    num_threads: Optional[int] = None  # Number of CPU threads to use during reconstruction


def check_args(args: CLIArgs):
    if args.feature == "r2d2" and args.matcher:
        if "NN" not in args.matcher:
            raise ValueError(
                f"Feature 'r2d2' only compatible with matchers: 'NN-ratio', 'NN-mutual'"
            )

    if args.matcher == "superpoint+lightglue" and args.feature:
        if args.feature not in [
            "superpoint_aachen",
            "superpoint_max",
            "superpoint_inloc",
        ]:
            raise ValueError(
                f"Matcher 'superpoint+lightglue' only compatible with features: 'superpoint_aachen', 'superpoint_max', 'superpoint_inloc'"
            )
    if args.matcher == "disk+lightglue" and args.feature:
        if args.feature != "disk":
            raise ValueError(
                f"Matcher 'disk+lightglue' only compatible with features: 'disk'"
            )
    if args.matcher == "aliked+lightglue" and args.feature:
        if args.feature != "aliked-n16":
            raise ValueError(
                f"Matcher 'aliked+lightglue' only compatible with features: 'aliked-n16'"
            )
    if args.matcher == "adalam" and args.feature:
        if args.feature not in ["sift", "sosnet"]:
            raise ValueError(
                f"Matcher 'adalam' only compatible with features: 'sift', 'sosnet'"
            )


def run(args: CLIArgs):
    check_args(args)
    
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
        if args.pairs:
            logger.info(f"Image pairing: {args.pairs}")
            if args.pairs == "exhaustive":
                pairs_from_exhaustive.main(
                    output=pairs_path,
                    image_list=image_list,
                    features=feature_path,
                )
            else:
                logger.info(f"Feature extraction for retrieval: {args.retrieval}")
                retrieval_path = extract_features.main(
                    conf=extract_features.confs[args.retrieval],
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
            matcher_conf = match_features.confs[args.matcher]
            if "weights" in matcher_conf["model"]:
                matcher_conf["model"]["weights"] = args.matcher_weights
                logger.info(f"Feature matching: {args.matcher} ({args.matcher_weights})")
            else:
                logger.info(f"Feature matching: {args.matcher}")
            match_features.main(
                conf=matcher_conf,
                pairs=pairs_path,
                features=feature_path,
                export_dir=hloc_dir,
                matches=matches_path,
                overwrite=args.overwrite,
            )
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
                mapper_options={"num_threads": args.num_threads or cpu_count()},
            )

            if args.global_bundle_adjustment:
                rec = pycolmap.Reconstruction()
                rec.read(sfm_dir)
                options = pycolmap.BundleAdjustmentOptions()
                pycolmap.bundle_adjustment(rec, options)
                if args.refine_principal_point:
                    options = pycolmap.BundleAdjustmentOptions(refine_principal_point=True)
                    pycolmap.bundle_adjustment(rec, options)
                rec.write(sfm_dir)


def main():
    run(tyro.cli(CLIArgs))


if __name__ == "__main__":
    main()
