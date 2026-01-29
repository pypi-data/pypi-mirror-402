import concurrent.futures
import math
import random
import shutil
import subprocess
from collections import Counter
from logging import Logger, getLevelNamesMapping
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import click

from .logger import get_logger

logger: Logger = get_logger()

XFADE_TRANSITIONS = [
    "fade",
    "slideleft",
    "slidedown",
    "smoothup",
    "smoothleft",
    "circleopen",
    "diagtl",
    "horzopen",
    "fadegrays",
    "pixelize",
    "hrwind",
    "diagbl",
    "diagtr",
]


@click.group()
@click.option(
    "--log-level",
    default="INFO",
    type=str,
    required=False,
    help="Sets the logging verbosity. Choose between"
    "DEBUG, INFO (default), WARNING, ERROR, or CRITICAL."
    "Can be uppercase or lowercase.",
)
def cli(log_level: str):
    global logger
    try:
        level_from_name = getLevelNamesMapping()[log_level.upper()]
        logger = get_logger(level_from_name)
    except Exception as e:
        logger.exception(e)


IN_DIR: Path
OUT_DIR: Path
CACHE_DIR = Path("./video-maker-cache")
THREADS = 12

MIN_SEGMENT_LENGTH = 5
MAX_SEGMENT_LENGTH = 9
MAX_SEGMENT_PADDING = 6


def run_in_bash(
    cmd: str,
    capture_output=False,
    check=False,
    text=False,
    shell=False,
):
    return subprocess.run(
        f"""bash -c '{cmd}'""",
        capture_output=capture_output,
        check=check,
        text=text,
        shell=shell,
    )


def nonrepeating_generator(source, desired_length):
    """
    Creates a generator that yields one item from `source`
    that is not equal to the last item yielded, up to
    `desired_length` times.
    """
    if not source:
        return
    if len(source) == 1 and desired_length > 1:
        raise ValueError("Cannot avoid repetition with only one unique string.")

    prev = None
    count = 0

    while count < desired_length:
        choices = [s for s in source if s != prev]
        if not choices:
            raise ValueError("No valid choices left to avoid repetition.")
        current = random.choice(choices)
        yield current
        prev = current
        count += 1


def seconds_to_timestamp(seconds: float):
    """Converts total seconds to a timestamp (HH:MM:SS.ms)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 100)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:02}"


def get_video_duration(file: Path):
    """Gets the duration of a video file in seconds."""
    logger.debug(f"Getting file length for {file}")
    try:
        return float(
            run_in_bash(
                f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{file}"',
                capture_output=True,
                check=True,
                text=True,
                shell=True,
            ).stdout.strip()
        )
    except Exception:
        logger.exception(f"Error getting file length for {file}")
        return 0.0


def generate_segment_lengths(file_length: float) -> List[float]:
    """Generates random segment lengths that sum up to the file length."""
    segment_lengths: List[float] = []
    while not math.isclose(sum(segment_lengths), file_length, rel_tol=1e-5):
        remaining_length = file_length - sum(segment_lengths)
        if remaining_length <= MAX_SEGMENT_PADDING:
            segment_lengths.append(remaining_length)
            break
        segment_lengths.append(random.uniform(MIN_SEGMENT_LENGTH, MAX_SEGMENT_LENGTH))
    logger.debug(f"Generated segment lengths: {segment_lengths}")
    return segment_lengths


def get_amplitude_from_stream(file: Path, start: float, duration: float):
    """Extracts the mean audio amplitude of a video segment directly from stream."""
    logger.debug(f"Analyzing amplitude for {file} at {start} for {duration}s")
    res = run_in_bash(
        f'ffmpeg -ss {start} -t {duration} -i "{file}" -filter:a volumedetect -f null -',
        shell=True,
        check=True,
        capture_output=True,
    ).stderr
    logger.debug(res)
    try:
        return float(res.decode().split("mean_volume: ")[1].split(" dB")[0])
    except IndexError:
        logger.warning(f"Could not determine volume for {file} segment. Defaulting to -91dB.")
        return -91.0


def build_input_flags(video_files: List[str]) -> str:
    return " ".join(f'-i "{video}"' for video in video_files)


def build_preprocess_filters(
    video_files: List[str],
) -> tuple[list[str], List[str], List[str]]:
    filters: List[str] = []
    video_labels: List[str] = []
    audio_labels: List[str] = []
    for i in range(len(video_files)):
        filters.append(
            f"[{i}:v]format=yuv420p,scale=1280:720,setpts=PTS-STARTPTS,fps=30[v{i}];"
        )
        filters.append(f"[{i}:a]aresample=async=1[a{i}];")
        video_labels.append(f"v{i}")
        audio_labels.append(f"a{i}")
    return filters, video_labels, audio_labels


def build_transition_filters_dynamic(
    filter_gen: Generator[str, Any, None],
    video_labels: List[str],
    audio_labels: List[str],
    durations: List[float],
    fade_duration: float = 1.0,
) -> tuple[List[str], List[str], str, str]:
    vf_filters: List[str] = []
    af_filters: List[str] = []

    offset = 0.0
    for i in range(len(video_labels) - 1):
        transition = next(filter_gen)
        offset += durations[i] - fade_duration

        out_v = f"vxf{i+1}"
        out_a = f"acf{i+1}"

        vf_filters.append(
            f"[{video_labels[i]}][{video_labels[i+1]}]xfade="
            f"transition={transition}:duration={fade_duration}:offset={offset:.2f}[{out_v}];"
        )
        video_labels[i + 1] = out_v

        af_filters.append(
            f"[{audio_labels[i]}][{audio_labels[i+1]}]acrossfade="
            f"d={fade_duration}:c1=tri:c2=tri[{out_a}];"
        )
        audio_labels[i + 1] = out_a

    return vf_filters, af_filters, video_labels[-1], audio_labels[-1]


def assemble_filter_complex(
    pre_filters: List[str],
    xfade_filters: List[str],
    audio_fades: List[str],
) -> str:
    return "\n".join(pre_filters + xfade_filters + audio_fades)


def run_ffmpeg_command(
    input_flags: str, filter_complex: str, output_file: Path, final_audio_label: str
) -> None:
    cmd: str = f"""
    ffmpeg -y {input_flags} \
    -filter_complex "{filter_complex}" \
    -map "[vxf{filter_complex.split("vxf")[-1].split("];")[0]}]" \
    -map "[{final_audio_label}]" \
    -c:v libx264 -preset slow \
    -c:a aac -b:a 128k "{output_file}"
    """
    run_in_bash(cmd, shell=True, check=True, capture_output=True)

def render_horizontal(decode_options: str, watermark_image: Path, output_file: Path):
    logger.info("Creating horizontal video...")
    run_in_bash(
        f'''ffmpeg -y {decode_options} -i "{CACHE_DIR / "out-unmarked.mp4"}" -i "{watermark_image}" \
        -filter_complex " \
        [1]format=rgba,colorchannelmixer=aa=0.5[logo]; \
        [0][logo]overlay=W-w-30:H-h-30:format=auto,format=yuv420p \
        " -c:a aac -b:a 128k "{output_file}"''',
        shell=True,
        check=True,
        capture_output=True,
    )
    logger.info(f"Horizontal video created at {output_file}")

def render_vertical(decode_options: str, watermark_image: Path, output_file: Path):
    logger.info("Creating vertical video...")
    run_in_bash(
        f'''ffmpeg -y {decode_options} -i "{CACHE_DIR / "out-unmarked.mp4"}" -i "{watermark_image}" \
        -filter_complex " \
        [0]crop=3/4*in_w:in_h[zoomed]; \
        [zoomed]split[original][copy]; \
        [copy]scale=-1:ih*(4/3)*(4/3),crop=w=ih*9/16,gblur=sigma=17:steps=5[blurred]; \
        [blurred][original]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2[vert]; \
        [vert][1]overlay=(W-w)/2:H-h-30,format=yuv420p \
        " -c:a aac -b:a 128k "{output_file}"''',
        shell=True,
        check=True,
        capture_output=True,
    )
    logger.info(f"Vertical video created at {output_file}")


@cli.command()
@click.option(
    "--input-dir",
    help="The input directory to get the source videos from.",
    type=click.Path(exists=True, resolve_path=True, path_type=Path),
)
@click.option(
    "--watermark-image",
    help="The path of the watermark image "
    "to overlay over the final output. "
    "It must exist. "
    "It will not be scaled, so it should be "
    "sized appropriately relative to the input.",
    type=click.Path(exists=True, resolve_path=True, path_type=Path),
)
@click.option(
    "--horiz-output-file",
    help="The path to output the final video to. "
    "It should not exist and must either be an absolute path "
    'or start with "./".',
    type=click.Path(exists=False, resolve_path=True, path_type=Path),
    required=False,
)
@click.option(
    "--vert-output-file",
    help="The path to output the final video to. "
    "It should not exist and must either be an absolute path "
    'or start with "./".',
    type=click.Path(exists=False, resolve_path=True, path_type=Path),
    required=False,
)
@click.option(
    "--decode-options",
    help="Options to pass to FFmpeg for some decode operations."
    "While optional, proper use of this option will significantly"
    "reduce processing time. Note that inclusion of any encoding options"
    "will cause this program to fail.",
    type=str,
    default="",
)
@click.option(
    "--num-segs",
    help="Total number of segments to concatenate in the output."
    "Controls the length of the final video.",
    type=int,
    default=10,
)
def run(
    input_dir: Path,
    watermark_image: Path,
    horiz_output_file: Optional[Path],
    vert_output_file: Optional[Path],
    decode_options: str,
    num_segs: int,
):
    """Main function that orchestrates the video processing pipeline."""
    logger.info("Starting video processing pipeline.")
    
    if not horiz_output_file and not vert_output_file:
         logger.error("No output file specified! Provide --horiz-output-file or --vert-output-file (or both).")
         # We could also use click constraints but checking here is fine for a quick refactor.
         return

    raw_videos = next(input_dir.walk())

    # Get the representative video (shortest video)
    representative_video = min(
        (Path(raw_videos[0], p) for p in raw_videos[2]), key=get_video_duration
    )

    logger.info(f"The representative video is: {representative_video}")

    representative_video_segments = generate_segment_lengths(
        get_video_duration(representative_video)
    )

    # Pre-create cache dir
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    
    # Analyze amplitudes of the representative video segments directly (without splitting)
    logger.info("Analyzing audio levels...")
    segment_amplitudes: Dict[int, float] = {}
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=THREADS) as executor:
        futures = {}
        for idx in range(len(representative_video_segments)):
            start_time = sum(representative_video_segments[:idx])
            duration = representative_video_segments[idx]
            futures[idx] = executor.submit(
                get_amplitude_from_stream,
                representative_video,
                start_time,
                duration
            )
        
        for idx, future in futures.items():
            segment_amplitudes[idx] = future.result()

    # Identify loudest segments
    highest = dict(Counter(segment_amplitudes).most_common(num_segs))
    loudest_seg_indexes: List[int] = sorted(list(highest.keys()))
    
    logger.info("Extracting selected segments...")
    video_files: List[str] = []
    
    # We need a directory for the chosen segments
    out_loudest_dir = Path(CACHE_DIR, "loudest")
    out_loudest_dir.mkdir(parents=True, exist_ok=True)
    
    with open(str(Path(CACHE_DIR, "list.txt")), "w") as f, \
         concurrent.futures.ProcessPoolExecutor(max_workers=THREADS) as split_executor:
         
        future_to_vid_path = {}
        
        for seg_idx in loudest_seg_indexes:
            # Pick a random video for this segment index
            random_vid_name = random.choice(raw_videos[2])
            random_vid_path = Path(raw_videos[0], random_vid_name)
            
            # Define output path for this specific clip
            final_clip_path = out_loudest_dir / f"seg_{seg_idx}_{random_vid_path.stem}{random_vid_path.suffix}"
            
            start_time = sum(representative_video_segments[:seg_idx])
            duration = representative_video_segments[seg_idx]

            future = split_executor.submit(
                run_in_bash,
                f"ffmpeg -nostats -loglevel 0 -y -ss {seconds_to_timestamp(start_time)} "
                f'-t {duration} -i "{random_vid_path}" '
                f'-c copy "{final_clip_path}"',
                check=True,
                shell=True
            )
            future_to_vid_path[future] = final_clip_path
            
            f.write(f"file '{final_clip_path}'\n")
            video_files.append(str(final_clip_path.resolve()))

        # Wait for all splits to finish
        for fut in concurrent.futures.as_completed(future_to_vid_path):
             try:
                 fut.result()
             except Exception as e:
                 logger.exception(f"Failed to extract segment: {e}")

    filter_gen = nonrepeating_generator(XFADE_TRANSITIONS, num_segs)

    input_flags: str = f"{decode_options} {build_input_flags(video_files)}"
    try:
        pre_filters, vlabels, alabels = build_preprocess_filters(video_files)
    except IndexError:
        logger.error("No video files generated? Aborting.")
        return
        
    durations = [get_video_duration(Path(vf)) for vf in video_files]
    
    vfades, afades, final_v, final_a = build_transition_filters_dynamic(
        filter_gen, vlabels, alabels, durations, 0.5
    )

    full_filter: str = assemble_filter_complex(pre_filters, vfades, afades)

    logger.info("Creating unmarked video (master)...")

    run_ffmpeg_command(
        output_file=CACHE_DIR
        / "out-unmarked.mp4",  # This file will have all the transitions without the overlayed logo
        input_flags=input_flags,
        filter_complex=full_filter,
        final_audio_label=final_a,
    )

    # Parallelize Final Output
    render_futures = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as render_executor:
        if horiz_output_file:
            render_futures.append(
                render_executor.submit(render_horizontal, decode_options, watermark_image, horiz_output_file)
            )
        
        if vert_output_file:
             render_futures.append(
                render_executor.submit(render_vertical, decode_options, watermark_image, vert_output_file)
            )
            
        for f in concurrent.futures.as_completed(render_futures):
            try:
                f.result()
            except Exception as e:
                logger.exception(f"Rendering failed: {e}")

    logger.info("Video processing pipeline completed.")
    logger.info("Cleaning up temporary files...")
    shutil.rmtree(CACHE_DIR)


if __name__ == "__main__":
    cli()
