# How computers see movement

A no-code Edinburgh AI workshop app by Conor O'Shea. Learners explore video frames, RGB pixels and skeleton coordinates, then invent a throw-detection rule and try it on practice and quiz clips.

This is a teaching interface around supplied examples. It does not run YOLO, train an LSTM or query an LLM. The independent production application is https://www.judoclipper.com/.

## Deploy with GitHub and Streamlit

1. Unzip this project. Create a new GitHub repository, for example `judo-vision-beginner-workshop`.
2. Upload the **contents** of the extracted folder. `app.py`, `core.py` and `requirements.txt` should be at the repository root. Include `data/` and `.streamlit/config.toml`. Don't upload just the ZIP file.
3. Open https://share.streamlit.io/ and connect the GitHub account/repository.
4. Create an app from that repository, select your branch and set the main file path to `app.py`.
5. In Advanced settings, select Python 3.11 if offered; this is the version used for local checks. Deploy the app.
6. Open every section and play both guided clips on the deployed version. Try the frame and pixel sliders, all skeleton views and a quiz submission.
7. Send the deployed URL back so it can be inserted into `BEGINNER-sports-vision-rnn-lstm.ipynb`.

No S3 bucket, API credentials, model weights, GPU or database is required. The app reads its media and pose files from the repo. Quiz progress lives in Streamlit session state; it isn't durable and may reset on refresh or reconnection. Do not rely on it as an attendance record.

Official deployment documentation: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## Run locally

Use a separate Python 3.11 environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or Linux/macOS:

```bash
source .venv/bin/activate
```

Then:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The dependency versions match the checked local environment. The app uses OpenCV headless for server-side video decoding and Pillow for drawing the exported poses. It has no live pose-inference dependency.

## Included experience

- Start page linking to Judo Clipper and explaining an attempt.
- Video playback and exact frame selection, with chronological frame strips.
- Pixel-position sliders, nearest-neighbour magnification, RGB values and eight-bit binary representations.
- Original/overlay/skeleton-only views, joint selection and numerical coordinates.
- Pre-rendered animations of the two guided skeleton sequences.
- A practice rule text box, predictions and label reveal.
- A final form that requires all answers before showing any result, then locks the submitted answers for that session.
- The original workshop GIF, preserved in an optional reference expander.

The frame slider is separate from the video player's playhead. This is deliberate: it inspects exact decoded frames without implying that Streamlit's player exposes frame-accurate seeking.

## Clip selection and remaining curation

Eight supplied clips are included: five positive and three negative examples. Roles within this learning activity are distinct from the research model's train/validation/test split.

| Role | Clip | Label | Note |
| --- | --- | --- | --- |
| Guided | attempt_id962 | Attempt | Selected for relatively clear pose alignment in sampled frames |
| Guided | no_throw_clip_2451 | No attempt | Standing interaction and gripping |
| Practice | attempt_id964 | Attempt | Throw example |
| Practice | no_throw_clip_2449 | No attempt | Provisional: broadcast change/pause |
| Practice | attempt_id960 | Attempt | Clear action, with a tracking failure during occlusion |
| Practice | attempt_id959 | Attempt | Additional standing/entry movement |
| Final quiz | attempt_id967 | Attempt | Kept out of the personal practice activity |
| Final quiz | no_throw_clip_2450 | No attempt | Provisional: broadcast change/pause |

**Before running the full workshop, replace the two provisional negatives with continuous standing fighting without an attempt or camera cut.** Additional negative examples would improve class balance. The prototype remains functional as supplied, but camera cuts and pauses make these two clips weaker examples of the intended discrimination.

The provided pose arrays also contain real selection errors. In some sampled frames from attempt_id960 and attempt_id964 a role jumps to the referee during a throw. The app draws those values honestly and explains the limitation. Do not describe the skeletons as perfect ground truth.

Labels identify at least one attempt in the entire clip; they do not locate it frame by frame. Positive IDs and pose rows come from the supplied research manifest. A small personal quiz score is not an estimate of the classifier's generalisation performance.

## Asset provenance and alignment

- `data/catalogue.json` records clip IDs, activity roles, binary labels, original array rows and research splits.
- `data/poses.npz` contains only the eight selected float32 `[210,68]` sequences. No need to commit the entire training dataset.
- `data/videos/` contains the corresponding original seven-second, 30fps H.264 videos.
- `data/skeletons/` contains generated pose animations for the two guided examples.
- `data/original_workshop.gif` preserves the older illustration. It is clearly labelled as belonging to the earlier per-frame task.

Pose coordinates are normalized to image width/height. They are not body-centred, and they aren't measurements in metres. Zero-valued unresolved coordinates are omitted from drawings. Player slots A/B are not guaranteed stable identities across a clip.

To add/replace clips, keep original IDs, use the same manifest row to retrieve the `[210,68]` pose array, update `poses.npz` and `catalogue.json`, copy the video, and check overlay alignment. Avoid putting the same clip into practice and final quiz. The two guided IDs also need a matching generated skeleton animation.

## Verification

Run the included checks with:

```bash
python -m unittest discover -s tests
```

Local checks decode the first and last frame of all eight videos, validate pose shapes, check pixel-to-binary values, omit unresolved skeleton points, and verify complete quiz submission and scoring. Separate Streamlit AppTest checks exercised every section, frame and pixel controls, all skeleton modes, practice reveal, incomplete quiz submission and a complete locked submission.

A live browser/deployed Streamlit session has not been inspected here. Check playback, layout and responsiveness after deployment, especially on the devices attendees will use.

## Teaching notes

Participants do not need to use Kaggle or run notebook cells. The beginner notebook is a reading/activity guide and the app contains the interactions.

The key progression is video as ordered pictures, pixels as colour numbers, joint coordinates as a smaller representation, and patterns across time. Emphasise that greater movement does not mean more binary ones. A skeleton representation reduces background detail but still contains camera/framing effects and pose errors.

Practice labels may inform rule revisions; final quiz labels appear only after all guesses are submitted. Explain that engineers likewise use validation results for model selection and reserve test data for a final check. Written rules in the app guide participants' own judgments, rather than training the underlying neural network.

## Credits and licence

Code and teaching materials: Conor O'Shea / Edinburgh AI, Apache License 2.0: https://www.apache.org/licenses/LICENSE-2.0.

This code licence does not apply to third-party broadcast footage. Videos and the original GIF retain their original rights. The package contains no credentials.
