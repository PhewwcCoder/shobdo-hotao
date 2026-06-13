# Third-Party Notices

ShobdoHotao is MIT licensed. It bundles and/or depends on the following
third-party components. Full license texts will be collected into this file as
part of Phase 3 release engineering. This list is the source of truth for what
must be attributed in a release.

| Component | Purpose | License | Notes |
|-----------|---------|---------|-------|
| PySide6 (Qt for Python) | Desktop UI | LGPLv3 / commercial | Dynamically linked; comply with LGPL relinking terms in builds. |
| DeepFilterNet (v3, 0.5.6) | Speech enhancement model + runtime | MIT / Apache-2.0 (verify per file) | Model weights bundled under `models/`. |
| PyTorch (CPU) | ML runtime for DeepFilterNet | BSD-3-Clause | CPU build only for the default release. |
| imageio-ffmpeg | Bundles the FFmpeg binary | Apache-2.0 (wrapper) | FFmpeg binary itself is LGPL/GPL — record the exact build's license. |
| FFmpeg | Audio/video decode, encode, extract, remux | LGPLv2.1+/GPL (build-dependent) | Confirm the imageio-ffmpeg build configuration and ship its license. Video path uses `-c:v copy` (no video re-encode) and the AAC/Opus audio encoders. |
| AAC encoder (FFmpeg native / libfdk) | Cleaned audio in MP4/MOV/MKV/AVI outputs | LGPL (native aac) / non-free (libfdk) | Default uses FFmpeg's **native** `aac` encoder to avoid non-free licensing. |
| libopus (via FFmpeg) | Cleaned audio in WebM outputs | BSD-3-Clause | Used because WebM forbids AAC. |
| libx264 (test fixture only) | Generating the short test video in integration tests | GPL | **Test-time only**; not required at runtime. The shipped app never re-encodes video. |
| torch 2.0.1 / torchaudio 2.0.2 (CPU) | DeepFilterNet runtime (pinned) | BSD-3-Clause | Pinned for DeepFilterNet 0.5.6 compatibility. |
| Noto Sans Bengali (or chosen Bangla font) | Bangla text rendering | SIL Open Font License 1.1 | Bundle font + OFL text under `ui/theme/assets/`. |
| Any bundled wallpaper/aero assets | Background art | TBD — must be verified | Only include royalty-free assets with attribution recorded here. |

**Action items before v1.0 (tracked in Phase 3):**
- [ ] Pin exact versions and capture each component's full license text.
- [ ] Verify the FFmpeg build's license flavor shipped by imageio-ffmpeg.
- [ ] Confirm DeepFilterNet weights' license and redistribution terms.
- [ ] Generate an SBOM and SHA-256 checksums for the release ZIP.
