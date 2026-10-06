<!--
  README.md -- Python utility scripts (catalog)
  Author:  Jibril Sulaiman
  Date:    2026-10-06
  What:    A catalog of small standalone Python tools, one folder each, with a short
           click-by-click section per tool: what it does, install, run, inputs and
           outputs, and the traps that came up when it was used.
  Why:     Each tool is too small for its own repo, but each solved a job that chat
           assistants' built-in file tools could not finish (timeouts, no OCR, no
           long-running jobs), so the working scripts are worth keeping in one place.
-->

# Python utility scripts

A small catalog of standalone Python tools for jobs that are too big or too slow for a
chat assistant's built-in file tools. Each tool lives in its own folder, runs on a normal
Windows laptop with no GPU and no API keys, and has its own step-by-step section below.

| Tool | What it does | Folder |
|---|---|---|
| **PDF text extractor with OCR** (written, not run) | Pulls every word out of a PDF, including text that only exists inside images, screenshots or scans | [`pdf-text-extractor-ocr/`](pdf-text-extractor-ocr/) |
| **Batch MP4 transcriber** | Turns a folder of hundreds or thousands of videos into `.txt` and `.srt` transcripts on the CPU, resumable | [`batch-mp4-transcriber/`](batch-mp4-transcriber/) |

## Why it exists

Both tools started as requests to a chat assistant ("extract all the text from this PDF,
even from the images", "transcribe all of these MP4s"). Both hit the same wall: the
assistant's sandbox is built for short jobs.

1. **Sandbox sessions time out.** OCR on a long, image-heavy PDF ran past the sandbox's
   limit. The chat showed **"Code interpreter session expired"**, and the download links
   for the files it had made stopped working, because they only live as long as the
   session.
2. **Partial runs come back looking complete.** A re-run in smaller batches finished and
   offered downloads, but the OCR sections were empty. Only the text layer had been
   extracted, so every word inside an image was missing.
3. **Long jobs don't fit at all.** A folder of well over a thousand short videos (tens of GB) is a
   multi-hour CPU job. No chat sandbox will hold it, and the upload alone isn't practical.

Running the same work locally has no time limit, keeps the output on your own disk, and can
be stopped and resumed. Neither tool needs an account, an API key or a paid service.

## What's in this repo

| Path | What it is | Where it runs |
|---|---|---|
| [`README.md`](README.md) | This guide | — |
| [`pdf-text-extractor-ocr/`](pdf-text-extractor-ocr/) | One script: PyMuPDF text layer + Tesseract OCR per page | Your computer, from PowerShell |
| [`batch-mp4-transcriber/`](batch-mp4-transcriber/) | One script: faster-whisper batch transcription with resume, sharding and an error log | Your computer, from PowerShell |

## Table of contents

- [1. Requirements](#1-requirements)
- [2. PDF text extractor with OCR](#2-pdf-text-extractor-with-ocr)
  - [Step 1: Install Tesseract](#step-1-install-tesseract)
  - [Step 2: Install the Python libraries](#step-2-install-the-python-libraries)
  - [Step 3: Run it on your PDF](#step-3-run-it-on-your-pdf)
  - [Step 4: Check the OCR sections](#step-4-check-the-ocr-sections)
- [3. Batch MP4 transcriber](#3-batch-mp4-transcriber)
  - [Step 1: Check your machine](#step-1-check-your-machine)
  - [Step 2: Install faster-whisper](#step-2-install-faster-whisper)
  - [Step 3: First run on the folder](#step-3-first-run-on-the-folder)
  - [Step 4: Speed it up](#step-4-speed-it-up)
  - [Step 5 (optional): Run parallel shards](#step-5-optional-run-parallel-shards)
  - [Step 6: Check the output](#step-6-check-the-output)
- [Troubleshooting](#troubleshooting)
- [Limits](#limits)
- [Security and privacy](#security-and-privacy)

## 1. Requirements

| Need | Version used | Notes |
|---|---|---|
| Windows 10 or 11 with PowerShell | — | Commands below are for PowerShell. They work on macOS/Linux with the same `python` lines. |
| Python | 3.13 (3.9 or newer should work) | Check with `python --version`. |
| Disk space | A few hundred MB per Whisper model | The transcriber downloads its model on first run. |
| GPU | Not needed | Both tools run on the CPU. |

Every command assumes you have opened PowerShell **in the folder that holds the script**
(in File Explorer, open the folder, click the address bar, type `powershell`, press Enter).

---

## 2. PDF text extractor with OCR

> ⚠️ **Written but not run.** This script was written for a real job (a long PDF of event
> details full of screenshots), but that job was finished another way, so this exact file
> has never been run end to end. The install steps are standard; treat the first run as a
> test.

Reads each page of a PDF twice: once for its normal text layer, and once as a ~150 DPI image
run through Tesseract OCR. Both go into one text file, page by page, so nothing that appears
on the page is missed, including words inside screenshots, scanned pages and graphics.

| Input | Output |
|---|---|
| One PDF, passed as the first argument (for example `document.pdf`) | `ALL_TEXT.txt`, written to the folder you run the command from |

Each page in `ALL_TEXT.txt` looks like this:

```text
=== PAGE 1 — DIRECT + OCR ===
<the page's normal text layer>

--- OCR TEXT (Page 1) ---
<everything Tesseract read from the page image, including text inside pictures>
```

### Step 1: Install Tesseract

About 5 minutes.

`pytesseract` is only a wrapper. The OCR engine itself, **Tesseract**, is a separate program
and must be installed first.

**1a. Install it.** Use whichever package manager you have:

| You have | Command |
|---|---|
| Chocolatey | `choco install tesseract` |
| winget (built into Windows 11) | `winget install UB-Mannheim.TesseractOCR` |
| macOS (Homebrew) | `brew install tesseract` |
| Ubuntu / Debian | `sudo apt-get install -y tesseract-ocr` |

**1b. Open a new PowerShell window** and check it:

```powershell
tesseract --version
```

Success looks like a first line starting `tesseract 5.` (any 4.x or 5.x is fine).

> ⚠️ **"The term 'tesseract' is not recognized".** The installer updated your PATH, but the
> window you're typing in still has the old one. Opening a new tab inside an editor's
> terminal (Cursor, VS Code) copies the same stale PATH. Either quit the editor completely
> and reopen it, or refresh PATH in the current window:
>
> ```powershell
> $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
> ```
>
> If it still isn't found, the Windows installer usually puts it in
> `C:\Program Files\Tesseract-OCR\`. Add that folder to your PATH.

✅ **Check:** `tesseract --version` prints a version number.

### Step 2: Install the Python libraries

About 2 minutes.

```powershell
pip install pytesseract pillow pymupdf
```

| Library | Used for |
|---|---|
| `pymupdf` (imported as `fitz`) | Opens the PDF, reads each page's text layer, renders each page to an image |
| `pillow` | Hands the rendered page image to Tesseract |
| `pytesseract` | Calls the Tesseract program installed in Step 1 |

✅ **Check:** `python -c "import fitz, pytesseract, PIL; print('ok')"` prints `ok`.

### Step 3: Run it on your PDF

About 1 minute to start; then roughly a few seconds per page.

**3a.** Download [`pdf-text-extractor-ocr/extract_all_text.py`](pdf-text-extractor-ocr/extract_all_text.py)
and save it in the same folder as your PDF.

**3b.** In PowerShell, in that folder, run it with your PDF's name in quotes:

```powershell
python extract_all_text.py "document.pdf"
```

Runs [`pdf-text-extractor-ocr/extract_all_text.py`](pdf-text-extractor-ocr/extract_all_text.py).

Success looks like one line when it finishes:

```text
Wrote ALL_TEXT.txt
```

There is no per-page progress output, so a long PDF just sits quietly until that line appears.

> ⚠️ **The output goes to the folder you ran the command from, not next to the PDF.** If you
> run it as `python extract_all_text.py "C:\path\to\folder\document.pdf"` from somewhere
> else, `ALL_TEXT.txt` lands in your current folder.

> ⚠️ **Every run overwrites `ALL_TEXT.txt`.** Rename it before running the script on a
> second PDF.

> ⚠️ **Put quotes around a file name with spaces.** Without them, only the first word
> reaches the script and it fails to open the file.

✅ **Check:** `ALL_TEXT.txt` exists and has one `=== PAGE N` heading per page of the PDF.

### Step 4: Check the OCR sections

About 2 minutes.

Open `ALL_TEXT.txt` and look under a few `--- OCR TEXT (Page N) ---` lines, especially on
pages you know are images or screenshots.

| You see | Meaning |
|---|---|
| Words under `--- OCR TEXT` on an image-only page | It worked. This is the text the chat sandbox missed. |
| Empty `--- OCR TEXT` sections on every page | Tesseract returned nothing. Re-check Step 1. |
| The same sentences in both the direct and OCR parts of a page | Expected. Pages with a text layer are read twice by design, so nothing slips through. De-duplicate afterwards if you need clean text. |
| Garbled OCR on small or blurry text | The render is ~150 DPI. See the tweak below. |

**Optional: higher accuracy for blurry images.** In the script, the render size is set by
`fitz.Matrix(2.1, 2.1)` (72 DPI × 2.1 ≈ 150 DPI). Changing both numbers to `4.17` renders at
about 300 DPI. It's slower, but it reads small and blurry text better.

✅ **Check:** an image-only page has readable words under its `--- OCR TEXT` line.

---

## 3. Batch MP4 transcriber

Transcribes every `.mp4` in one folder with [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
on the CPU (int8). For each clip it writes a plain `.txt` and a timestamped `.srt` subtitle file,
and appends the text to one combined file. It skips any clip that already has a `.txt`, so you
can stop it with **Ctrl+C** at any time and rerun the same command to carry on.

It was used on a folder of well over a thousand short clips (tens of GB) on a laptop with an
AMD integrated GPU and no NVIDIA card. All but one clip transcribed, and the one failure was
logged without stopping the run.

**Command-line options** (all optional):

| Flag | Default | What it does |
|---|---|---|
| `--src` | `.` (the current folder) | Folder containing the `.mp4` files. Subfolders are not searched. |
| `--model` | `small` | Whisper model: `tiny`, `base`, `small`, `medium`, or the English-only `tiny.en`, `base.en`, `small.en`, `medium.en`. Bigger is slower and more accurate. |
| `--lang` | `en` | Forces a language code. Use `auto` to detect the language per clip. |
| `--beam` | `1` | Beam size. `1` is greedy (fastest). `5` is more accurate and slower. |
| `--threads` | `0` (auto) | CPU threads for the model. Try your physical core count, divided by `--of` if you run shards. |
| `--of` | `1` | Total number of parallel shards (terminals) you are running. |
| `--shard` | `0` | This terminal's shard number, from `0` to `--of` minus 1. |

**Output**, all inside a `transcripts\` subfolder of `--src`:

| File | Contents |
|---|---|
| `<clip name>.txt` | Plain transcript, one Whisper segment per line |
| `<clip name>.srt` | Same text with `HH:MM:SS,mmm --> HH:MM:SS,mmm` timestamps, for subtitles or jumping to a moment |
| `_ALL_TRANSCRIPTS.txt` | Every transcript appended, each under a `===== <clip name>.mp4 (lang=en) =====` heading |
| `_ALL_TRANSCRIPTS_shard0.txt`, `_shard1`, ... | Used instead of the file above when you run with `--of` greater than 1 (Step 5) |
| `_errors.log` | One line per clip that failed: the file name, a tab, and the error |

### Step 1: Check your machine

About 2 minutes.

**1a.** Check Python:

```powershell
python --version
```

**1b.** Check your graphics card:

```powershell
(Get-CimInstance Win32_VideoController).Name
```

**1c.** Check your physical core count (you'll use it for `--threads`):

```powershell
(Get-CimInstance Win32_Processor).NumberOfCores
```

| 1b shows | What it means |
|---|---|
| AMD Radeon, Intel Iris/UHD/Arc, or any non-NVIDIA card | Run on the CPU, as this script does. These GPUs can't speed up faster-whisper on Windows. |
| An NVIDIA GeForce/RTX card | You *could* run 10× or more faster on the GPU, but this script is set to CPU (`device="cpu"`). It still works as is. |

✅ **Check:** you know your Python version and your core count.

### Step 2: Install faster-whisper

About 2 minutes.

```powershell
pip install faster-whisper
```

✅ **Check:** `python -c "import faster_whisper; print(faster_whisper.__version__)"` prints a
version number (this was built with `1.2.1`).

### Step 3: First run on the folder

About 5 minutes to start, then hours for a large folder.

**3a.** Put all the `.mp4` files in one folder (for example `C:\path\to\clips`). The script
only looks at that folder, not at subfolders.

**3b.** Download [`batch-mp4-transcriber/transcribe_all.py`](batch-mp4-transcriber/transcribe_all.py)
and save it anywhere, for example in the same folder.

**3c.** Run it, pointing `--src` at the clips folder:

```powershell
python transcribe_all.py --src "C:\path\to\clips"
```

Runs [`batch-mp4-transcriber/transcribe_all.py`](batch-mp4-transcriber/transcribe_all.py).

The first run downloads the model, which takes a few minutes. You'll first see:

```text
Loading model 'small' (int8, CPU)... first run downloads it, please wait.
```

You may also see two warnings, and **both are harmless**:

| Warning | What it means |
|---|---|
| *"You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN..."* | The model download from Hugging Face isn't signed in. It still downloads. No token needed. |
| *"`huggingface_hub` cache-system uses symlinks by default... your machine does not support them"* | Windows without Developer Mode can't make symlinks, so the model cache uses a little more disk. Ignore it. |

Success looks like this, one pair of lines per clip:

```text
Model ready. 500 clips to process.

[1/500] clip-0001.mp4
    done in  4.2s  |  1 transcribed, 0 skipped, 0 failed  |  ETA ~  115 min
```

**3d.** After 15 to 20 clips, open two or three `.txt` files in `transcripts\` and read them.
If the speech reads correctly, let it run.

> ⚠️ **Some clips take 30 to 140 seconds instead of 3.** In the real run, most clips finished
> in 1 to 4 seconds, but every so often one took 35, 85, 115 or 141 seconds, and those
> outliers pushed the ETA past 1,500 minutes (about 25 hours). They were music-only or
> unclear-speech clips where Whisper falls into a repetition loop. The script now passes
> `condition_on_previous_text=False` and uses greedy decoding (`--beam 1`) by default, which
> stops the loops. Step 4 covers the rest of the speed-up.

✅ **Check:** `transcripts\` is filling with `.txt` and `.srt` pairs, and the text matches what
is said in the clips.

### Step 4: Speed it up

About 2 minutes.

**4a.** Press **Ctrl+C**. You'll see:

```text
Interrupted. Progress saved. Rerun the same command to resume.
```

**4b.** Rerun with an English-only model and your core count from Step 1c:

```powershell
python transcribe_all.py --src "C:\path\to\clips" --model base.en --threads 8
```

Runs [`batch-mp4-transcriber/transcribe_all.py`](batch-mp4-transcriber/transcribe_all.py).

Clips that already have a `.txt` are skipped and counted under `skipped`.

| Change | Effect |
|---|---|
| `--model base.en` instead of `small` | About 2× faster. The `.en` models are faster *and* more accurate than the multilingual ones when all the audio is English. |
| `--threads <your cores>` | Lets the model use every physical core. |
| `--beam 1` (already the default) | Greedy decoding, about 2× faster than beam 5, with little accuracy loss for this use. |

With these settings, the remaining batch went from an ETA of about 24 hours to a few hours.

> ⚠️ **Right after a resume, the ETA is too optimistic.** The rate counts skipped clips, which
> take no time, so the first ETAs after a rerun are low. It settles after a few dozen new
> clips.

> ⚠️ **The clip in progress when you press Ctrl+C is redone.** Its `.txt` is only written when
> it finishes, so the next run starts it again. Nothing is lost.

✅ **Check:** "done in" times are mostly a few seconds and the ETA is in hours, not days.

### Step 5 (optional): Run parallel shards

About 5 minutes.

One transcription of a short clip doesn't keep every core busy. Running several copies at
once, each on a different slice of the files, finishes sooner overall.

**5a.** Stop any running copy with **Ctrl+C**.

**5b.** Open **3** separate PowerShell windows. In each one, run the same command with a
different `--shard` number. With 8 cores, give each about a third:

```powershell
python transcribe_all.py --src "C:\path\to\clips" --model base.en --of 3 --shard 0 --threads 3
```

```powershell
python transcribe_all.py --src "C:\path\to\clips" --model base.en --of 3 --shard 1 --threads 3
```

```powershell
python transcribe_all.py --src "C:\path\to\clips" --model base.en --of 3 --shard 2 --threads 3
```

Runs [`batch-mp4-transcriber/transcribe_all.py`](batch-mp4-transcriber/transcribe_all.py).

Shard `0` takes clips 1, 4, 7..., shard `1` takes 2, 5, 8..., and so on (by sorted file name).
Each window shows its own count, such as `[1/167]` for 500 clips.

> ⚠️ **Each shard writes its own combined file** (`_ALL_TRANSCRIPTS_shard0.txt` and so on),
> not `_ALL_TRANSCRIPTS.txt`. Join them yourself when they're done. The per-clip `.txt` and
> `.srt` files are the same either way.

> ⚠️ **Don't run a sharded and an unsharded copy at the same time.** They'd pick up the same
> clips, and the combined files would get duplicate entries.

✅ **Check:** all three windows are printing "done in" lines with different clip names.

### Step 6: Check the output

About 5 minutes.

When a run finishes it prints:

```text
Finished. 499 transcribed, 0 already done, 1 failed.
Transcripts in: C:\path\to\clips\transcripts
Combined file : C:\path\to\clips\transcripts\_ALL_TRANSCRIPTS.txt
```

**6a.** Count the per-clip transcripts and compare with the number of videos:

```powershell
(Get-ChildItem "C:\path\to\clips\transcripts" -Filter *.txt | Where-Object { $_.Name -notlike "_*" }).Count
(Get-ChildItem "C:\path\to\clips" -Filter *.mp4).Count
```

**6b.** If they differ, open `transcripts\_errors.log` to see which clips failed and why.
Rerunning the same command retries only those, because they have no `.txt` yet.

> ⚠️ **The combined file is append-only.** If you delete a clip's `.txt` to redo it, the rerun
> adds a second copy of that clip to `_ALL_TRANSCRIPTS.txt`. Remove the old block by hand, or
> rebuild the combined file from the per-clip `.txt` files.

✅ **Check:** the two counts match, or every missing clip is listed in `_errors.log`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `TesseractNotFoundError` / *"tesseract is not installed or it's not in your PATH"* | Tesseract program missing, or the terminal has a stale PATH | [PDF Step 1](#step-1-install-tesseract) |
| `ModuleNotFoundError: No module named 'fitz'` | PyMuPDF not installed | [PDF Step 2](#step-2-install-the-python-libraries): `pip install pymupdf` |
| `IndexError: list index out of range` from `extract_all_text.py` | No PDF name was given after the script name | [PDF Step 3](#step-3-run-it-on-your-pdf) |
| `ALL_TEXT.txt` has empty OCR sections | Tesseract returned nothing | [PDF Step 4](#step-4-check-the-ocr-sections) |
| Can't find `ALL_TEXT.txt` | It's in the folder you ran the command from | [PDF Step 3](#step-3-run-it-on-your-pdf) |
| `ERROR: source folder not found` | `--src` path is wrong, or has spaces and no quotes | [Transcriber Step 3](#step-3-first-run-on-the-folder) |
| `No .mp4 files found in ...` | Clips are in subfolders, or have another extension | Move them into one folder, [Transcriber Step 3](#step-3-first-run-on-the-folder) |
| ETA of a day or more, with some clips taking 30–140 s | Repetition loops on music-only clips, or a large model | [Transcriber Step 4](#step-4-speed-it-up) |
| HF Hub / symlink warnings at start | Harmless | [Transcriber Step 3](#step-3-first-run-on-the-folder) |
| Duplicate entries in `_ALL_TRANSCRIPTS.txt` | A clip was redone, or two copies ran at once | [Transcriber Step 6](#step-6-check-the-output), [Step 5](#step-5-optional-run-parallel-shards) |
| `pip` or `python` not recognised | Python not installed or not on PATH | Install Python from https://www.python.org/downloads/ and tick **Add python.exe to PATH** (wording may differ) |

## Limits

- **PDF extractor:** one PDF per run, fixed output name, no progress output. OCR language is
  Tesseract's default (English). Very large PDFs hold every page's text in memory until the end.
- **Transcriber:** `.mp4` only, one folder, no subfolders. CPU only, as written. Speaker names
  are not detected; the transcript is one block of speech per clip. Accuracy depends on the
  model. Music, crosstalk and heavy background noise come out rough.

## Security and privacy

- Neither tool sends your files anywhere. Everything runs on your machine.
- The only network access is the transcriber's one-time model download from Hugging Face.
- No keys, tokens or accounts are needed or stored.
- Only process documents and recordings you have the right to use.

Built by [Jibril Sulaiman](https://github.com/carljibrilsulaimanii).
