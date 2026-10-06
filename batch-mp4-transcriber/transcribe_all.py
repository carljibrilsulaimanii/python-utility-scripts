# transcribe_all.py
# Author: Jibril Sulaiman
# What:   Batch-transcribes every .mp4 in a folder with faster-whisper on the CPU. Writes
#         one .txt and one .srt (timestamped subtitles) per clip into a transcripts\
#         subfolder, and appends every transcript to one combined _ALL_TRANSCRIPTS.txt.
# Why:    A folder of 1,000+ short videos needed to become searchable text on a laptop
#         with no NVIDIA GPU. faster-whisper's int8 CPU mode is the fastest local option,
#         and a multi-hour batch has to survive Ctrl+C, crashes and reruns.
# Run:    pip install faster-whisper
#         python transcribe_all.py --src "C:\path\to\clips" --model base.en --threads 8
"""
Batch-transcribe every .mp4 in a folder with faster-whisper (CPU).
Resumable: skips any clip whose .txt already exists. Safe to Ctrl+C and rerun.

Usage:
    python transcribe_all.py
    python transcribe_all.py --model base --lang en
    python transcribe_all.py --src "C:\\path\\to\\clips"
"""

import argparse
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel


def fmt_ts(seconds: float) -> str:
    """seconds -> SRT timestamp HH:MM:SS,mmm"""
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".",
                    help="Folder containing the .mp4 files (default: the current folder)")
    ap.add_argument("--model", default="small",
                    help="Whisper model: tiny, base, small, medium (bigger = slower + more accurate)")
    ap.add_argument("--lang", default="en",
                    help="Force a language code (e.g. en), or 'auto' to detect per clip")
    ap.add_argument("--beam", type=int, default=1,
                    help="Beam size. 1 = greedy (fastest). 5 = more accurate, slower.")
    ap.add_argument("--threads", type=int, default=0,
                    help="CPU threads (0 = auto). Try physical cores divided by --of.")
    ap.add_argument("--of", type=int, default=1,
                    help="Total number of parallel shards (terminals) you are running.")
    ap.add_argument("--shard", type=int, default=0,
                    help="This shard's index, 0-based (0 to --of minus 1).")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.is_dir():
        print(f"ERROR: source folder not found: {src}")
        return 1

    out_dir = src / "transcripts"
    out_dir.mkdir(exist_ok=True)
    suffix = "" if args.of == 1 else f"_shard{args.shard}"
    master = out_dir / f"_ALL_TRANSCRIPTS{suffix}.txt"

    clips = sorted(src.glob("*.mp4"))
    if args.of > 1:
        clips = [c for i, c in enumerate(clips) if i % args.of == args.shard]
    total = len(clips)
    if total == 0:
        print(f"No .mp4 files found in {src}")
        return 1

    language = None if args.lang.lower() == "auto" else args.lang

    print(f"Loading model '{args.model}' (int8, CPU)... first run downloads it, please wait.")
    model = WhisperModel(args.model, device="cpu", compute_type="int8",
                         cpu_threads=args.threads)
    print(f"Model ready. {total} clips to process.\n")

    done = skipped = failed = 0
    t_start = time.time()

    for i, clip in enumerate(clips, 1):
        txt_path = out_dir / (clip.stem + ".txt")
        srt_path = out_dir / (clip.stem + ".srt")

        if txt_path.exists():
            skipped += 1
            continue

        print(f"[{i}/{total}] {clip.name}", flush=True)
        t0 = time.time()
        try:
            segments, info = model.transcribe(
                str(clip),
                language=language,
                vad_filter=True,                   # skip silence -> faster
                beam_size=args.beam,               # 1 = greedy, much faster
                condition_on_previous_text=False,  # stops runaway repetition loops
            )

            lines, srt_chunks = [], []
            for n, seg in enumerate(segments, 1):
                text = seg.text.strip()
                lines.append(text)
                srt_chunks.append(
                    f"{n}\n{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}\n{text}\n"
                )

            body = "\n".join(lines).strip()
            txt_path.write_text(body + "\n", encoding="utf-8")
            srt_path.write_text("\n".join(srt_chunks), encoding="utf-8")

            with master.open("a", encoding="utf-8") as fh:
                fh.write(f"\n===== {clip.name} (lang={info.language}) =====\n{body}\n")

            done += 1
            dt = time.time() - t0
            elapsed = time.time() - t_start
            rate = (done + skipped) / elapsed * 60 if elapsed else 0
            remaining = total - i
            eta_min = remaining / rate if rate else 0
            print(f"    done in {dt:4.1f}s  |  {done} transcribed, {skipped} skipped, "
                  f"{failed} failed  |  ETA ~{eta_min:5.0f} min", flush=True)

        except KeyboardInterrupt:
            print("\nInterrupted. Progress saved. Rerun the same command to resume.")
            return 130
        except Exception as e:
            failed += 1
            print(f"    FAILED: {e}", flush=True)
            (out_dir / "_errors.log").open("a", encoding="utf-8").write(
                f"{clip.name}\t{e}\n"
            )

    print(f"\nFinished. {done} transcribed, {skipped} already done, {failed} failed.")
    print(f"Transcripts in: {out_dir}")
    print(f"Combined file : {master}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
