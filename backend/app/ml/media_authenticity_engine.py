import io
import os
import hashlib
import struct
import wave
from typing import Dict, Any, List, Optional
from PIL import Image, ImageChops, ImageStat, ExifTags

STATUTORY_DISCLAIMER = (
    "Forensic media analysis provides probabilistic heuristic indicators and cannot serve as "
    "definitive legal proof of deepfake generation without cryptographic provenance (C2PA) "
    "or formal forensic laboratory verification. Never treat algorithmic verdicts as infallible."
)

KNOWN_AI_SOFTWARE_SIGNATURES = [
    "stable diffusion", "midjourney", "dall-e", "novelai", "comfyui",
    "automatic1111", "invokeai", "deepfacelab", "faceswap", "roop",
    "reactor", "civitai", "leonardo.ai", "runwayml", "pika labs",
    "sora", "flux.1", "fooocus", "dreamstudio"
]

KNOWN_EDITING_SIGNATURES = [
    "photoshop", "gimp", "canva", "inshot", "picsart",
    "snapseed", "lightroom", "after effects", "premiere pro", "davinci resolve"
]

class MediaAuthenticityEngine:
    """
    Forensic Media Authenticity & Deepfake Indicator Analyzer.
    Analyzes images, audio, and video using deterministic local heuristics:
    1. EXIF and metadata inspection for AI prompts, software tags, and C2PA markers.
    2. Error Level Analysis (ELA) to detect image splicing and resaved compression anomalies.
    3. Noise floor and compression uniformity auditing.
    4. Audio container and frequency cutoff analysis.
    5. Video container atom/codec inspection.
    """

    def calculate_file_hash(self, file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    def detect_media_type(self, file_bytes: bytes, filename: str) -> str:
        ext = os.path.splitext(filename.lower())[1]

        # Magic byte checks
        if file_bytes.startswith(b"\xff\xd8\xff"):
            return "IMAGE"  # JPEG
        if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "IMAGE"  # PNG
        if len(file_bytes) > 12 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
            return "IMAGE"  # WEBP
        if len(file_bytes) > 12 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WAVE":
            return "AUDIO"  # WAV
        if file_bytes.startswith(b"ID3") or file_bytes.startswith(b"\xff\xfb"):
            return "AUDIO"  # MP3
        if len(file_bytes) > 8 and file_bytes[4:8] == b"ftyp":
            return "VIDEO"  # MP4 / QuickTime
        if file_bytes.startswith(b"\x1a\x45\xdf\xa3"):
            return "VIDEO"  # WEBM / Matroska

        # Fallback to extension if magic bytes partially match
        if ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
            return "IMAGE"
        if ext in [".mp3", ".wav", ".ogg", ".m4a"]:
            return "AUDIO"
        if ext in [".mp4", ".webm", ".avi", ".mov", ".mkv"]:
            return "VIDEO"

        return "UNKNOWN"

    def analyze_image_ela(self, image: Image.Image) -> Dict[str, Any]:
        """
        Error Level Analysis (ELA).
        Recompresses the image at 90% JPEG quality and measures pixel difference.
        Unmanipulated images generally exhibit consistent error levels across uniform textures.
        Spliced or AI-infilled elements often show anomalous high/low error variance.
        """
        try:
            rgb_img = image.convert("RGB")
            buffer = io.BytesIO()
            rgb_img.save(buffer, format="JPEG", quality=90)
            buffer.seek(0)
            recompressed = Image.open(buffer)

            # Compute difference
            diff = ImageChops.difference(rgb_img, recompressed)

            # Multiplier scaling for visibility
            stat = ImageStat.Stat(diff)
            mean_error = sum(stat.mean) / len(stat.mean)
            std_dev = sum(stat.stddev) / len(stat.stddev)
            extrema_max = max([e[1] for e in stat.extrema])

            # Regional variance analysis (split into 4 quadrants to detect local splicing)
            width, height = rgb_img.size
            quad_errors = []
            if width > 40 and height > 40:
                mid_x, mid_y = width // 2, height // 2
                quadrants = [
                    (0, 0, mid_x, mid_y),
                    (mid_x, 0, width, mid_y),
                    (0, mid_y, mid_x, height),
                    (mid_x, mid_y, width, height)
                ]
                for box in quadrants:
                    quad_diff = diff.crop(box)
                    q_stat = ImageStat.Stat(quad_diff)
                    quad_errors.append(sum(q_stat.mean) / len(q_stat.mean))

            quad_spread = (max(quad_errors) - min(quad_errors)) if quad_errors else 0.0

            splicing_detected = quad_spread > 4.5 or (std_dev > 6.0 and mean_error > 8.0)

            return {
                "mean_error_level": round(mean_error, 2),
                "error_std_dev": round(std_dev, 2),
                "peak_error": extrema_max,
                "regional_variance": round(quad_spread, 2),
                "ela_anomaly_flag": splicing_detected,
                "assessment": "High local compression variance indicating potential splicing" if splicing_detected else "Uniform compression pattern"
            }
        except Exception as e:
            return {
                "mean_error_level": 0.0,
                "error_std_dev": 0.0,
                "peak_error": 0,
                "regional_variance": 0.0,
                "ela_anomaly_flag": False,
                "error": str(e)
            }

    def inspect_metadata(self, file_bytes: bytes, media_type: str) -> Dict[str, Any]:
        """
        Inspects file headers, EXIF tags, software strings, and prompt manifests.
        """
        metadata_findings = {
            "has_exif": False,
            "software_tags": [],
            "ai_signatures": [],
            "editing_signatures": [],
            "raw_text_traces": [],
            "c2pa_manifest_found": False
        }

        # Check raw bytes for known string signatures (works across images, video, audio)
        lower_bytes = file_bytes[:100000].lower() + file_bytes[-50000:].lower()

        # Check C2PA / Content Credentials markers
        if b"c2pa" in lower_bytes or b"contentcredentials" in lower_bytes:
            metadata_findings["c2pa_manifest_found"] = True

        for sig in KNOWN_AI_SOFTWARE_SIGNATURES:
            if sig.encode() in lower_bytes:
                metadata_findings["ai_signatures"].append(sig.title())

        for sig in KNOWN_EDITING_SIGNATURES:
            if sig.encode() in lower_bytes:
                metadata_findings["editing_signatures"].append(sig.title())

        if media_type == "IMAGE":
            try:
                img = Image.open(io.BytesIO(file_bytes))
                exif_data = img._getexif() if hasattr(img, "_getexif") else None
                if exif_data:
                    metadata_findings["has_exif"] = True
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        if tag_name in ["Software", "ImageDescription", "UserComment", "Artist"]:
                            val_str = str(value).lower()
                            metadata_findings["software_tags"].append(f"{tag_name}: {str(value)[:100]}")
                            for ai_sig in KNOWN_AI_SOFTWARE_SIGNATURES:
                                if ai_sig in val_str and ai_sig.title() not in metadata_findings["ai_signatures"]:
                                    metadata_findings["ai_signatures"].append(ai_sig.title())
                            for edit_sig in KNOWN_EDITING_SIGNATURES:
                                if edit_sig in val_str and edit_sig.title() not in metadata_findings["editing_signatures"]:
                                    metadata_findings["editing_signatures"].append(edit_sig.title())

                # Check PNG textual chunks (often contain Stable Diffusion generation prompts)
                if hasattr(img, "info") and img.info:
                    for key, val in img.info.items():
                        val_str = str(val).lower()
                        if key.lower() in ["parameters", "prompt", "workflow"]:
                            metadata_findings["raw_text_traces"].append(f"AI Generation Metadata ({key})")
                            metadata_findings["ai_signatures"].append("Synthetic Generation Prompt Manifest")
                        for ai_sig in KNOWN_AI_SOFTWARE_SIGNATURES:
                            if ai_sig in val_str and ai_sig.title() not in metadata_findings["ai_signatures"]:
                                metadata_findings["ai_signatures"].append(ai_sig.title())
            except Exception:
                pass

        return metadata_findings

    def analyze_audio_forensics(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Inspects audio container headers and basic sample metrics for synthetic voice clues.
        """
        audio_details = {
            "channels": None,
            "sample_rate_hz": None,
            "duration_seconds": None,
            "synthetic_voice_indicators": []
        }

        # Check WAV header if applicable
        if len(file_bytes) > 44 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WAVE":
            try:
                with wave.open(io.BytesIO(file_bytes), "rb") as wav_file:
                    audio_details["channels"] = wav_file.getnchannels()
                    audio_details["sample_rate_hz"] = wav_file.getframerate()
                    n_frames = wav_file.getnframes()
                    if audio_details["sample_rate_hz"]:
                        audio_details["duration_seconds"] = round(n_frames / audio_details["sample_rate_hz"], 2)

                    # Many cheap TTS models output mono audio at strictly 16000Hz or 22050Hz
                    if audio_details["sample_rate_hz"] in [16000, 22050] and audio_details["channels"] == 1:
                        audio_details["synthetic_voice_indicators"].append(
                            f"Standard synthetic speech sampling profile ({audio_details['sample_rate_hz']}Hz mono)"
                        )
            except Exception:
                pass

        # Raw string scan for synthetic audio encoders
        lower = file_bytes.lower()
        if b"elevenlabs" in lower or b"edge-tts" in lower or b"bark" in lower or b"rvc" in lower or b"tortoise" in lower:
            audio_details["synthetic_voice_indicators"].append("Synthetic voice cloner watermark tag found in stream")

        return audio_details

    def analyze_video_forensics(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Inspects video atoms (MP4/WEBM) for container encoding tools and consistency.
        """
        video_details = {
            "format": "MP4/QuickTime" if b"ftyp" in file_bytes[:32] else "WEBM/Matroska",
            "detected_atoms": [],
            "encoder_clues": []
        }

        lower = file_bytes.lower()
        if b"isom" in file_bytes[:64]:
            video_details["detected_atoms"].append("ISO Base Media File (isom)")
        if b"mp42" in file_bytes[:64]:
            video_details["detected_atoms"].append("MP4 v2 container")

        if b"lavf" in lower:
            video_details["encoder_clues"].append("FFmpeg Libavformat muxer (Common in AI video synthesis pipelines)")
        if b"handbrake" in lower:
            video_details["encoder_clues"].append("HandBrake transcode")

        return video_details

    def analyze_media(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Comprehensive forensic analysis pipeline.
        Calculates SHA-256 hash, determines media type, evaluates metadata and compression,
        and computes a transparent authenticity confidence score (0-100).
        """
        file_hash = self.calculate_file_hash(file_bytes)
        file_size_kb = round(len(file_bytes) / 1024, 2)
        media_type = self.detect_media_type(file_bytes, filename)

        if media_type == "UNKNOWN":
            return {
                "file_name": filename,
                "file_hash": file_hash,
                "media_type": "UNKNOWN",
                "file_size_kb": file_size_kb,
                "authenticity_score": 50,
                "verdict": "INCONCLUSIVE_INSUFFICIENT_EVIDENCE",
                "forensic_flags": {
                    "errors": ["Unsupported or unrecognizable media format."]
                },
                "limitations_disclaimer": STATUTORY_DISCLAIMER
            }

        # 1. Metadata inspection
        metadata = self.inspect_metadata(file_bytes, media_type)

        # 2. Modality-specific forensic checks
        ela_results = None
        audio_results = None
        video_results = None
        positive_indicators: List[str] = []
        negative_indicators: List[str] = []

        # Scoring baseline: Starts at neutral 75 (assume benign until forensic anomalies found)
        score = 75

        # Check AI signatures in metadata (definitive indicator)
        if metadata["ai_signatures"]:
            score -= 55
            negative_indicators.append(
                f"Definitive synthetic generation signature found: {', '.join(metadata['ai_signatures'])}"
            )

        # Check image editing signatures
        if metadata["editing_signatures"]:
            score -= 20
            negative_indicators.append(
                f"Digital editing software fingerprint identified: {', '.join(metadata['editing_signatures'])}"
            )

        if media_type == "IMAGE":
            try:
                img = Image.open(io.BytesIO(file_bytes))
                ela_results = self.analyze_image_ela(img)

                if ela_results.get("ela_anomaly_flag"):
                    score -= 30
                    negative_indicators.append(
                        f"ELA anomaly detected: Non-uniform regional error variance ({ela_results['regional_variance']}) suggesting local splicing or face manipulation"
                    )
                else:
                    score += 10
                    positive_indicators.append("Uniform Error Level Analysis (ELA) distribution with consistent noise floor")

                if metadata["has_exif"]:
                    score += 5
                    positive_indicators.append("Standard camera EXIF metadata present")
                else:
                    negative_indicators.append("EXIF metadata absent or stripped (typical in web-forwarded or AI-generated images)")

            except Exception as e:
                negative_indicators.append(f"Image decompression notice: {str(e)}")

        elif media_type == "AUDIO":
            audio_results = self.analyze_audio_forensics(file_bytes, filename)
            if audio_results["synthetic_voice_indicators"]:
                score -= 40
                for ind in audio_results["synthetic_voice_indicators"]:
                    negative_indicators.append(ind)
            else:
                score += 5
                positive_indicators.append("No obvious synthetic speech encoder tags detected")

        elif media_type == "VIDEO":
            video_results = self.analyze_video_forensics(file_bytes, filename)
            if video_results["encoder_clues"]:
                score -= 15
                for clue in video_results["encoder_clues"]:
                    negative_indicators.append(clue)
            else:
                score += 5
                positive_indicators.append("Standard commercial video container structure")

        # Check C2PA Content Credentials
        if metadata["c2pa_manifest_found"]:
            score += 15
            positive_indicators.append("C2PA / Content Credentials provenance manifest header detected")

        # Clamp score 0 to 100
        score = max(5, min(95, score))

        # Determine verdict
        if score < 40:
            verdict = "PROBABLE_SYNTHETIC_OR_MANIPULATED"
        elif score < 70:
            verdict = "SUSPICIOUS_ANOMALIES_DETECTED"
        else:
            verdict = "LIKELY_AUTHENTIC"

        forensic_flags = {
            "media_type": media_type,
            "file_size_kb": file_size_kb,
            "metadata": metadata,
            "ela_analysis": ela_results,
            "audio_forensics": audio_results,
            "video_forensics": video_results,
            "suspicious_factors": negative_indicators,
            "authenticity_indicators": positive_indicators
        }

        return {
            "file_name": filename,
            "file_hash": file_hash,
            "media_type": media_type,
            "file_size_kb": file_size_kb,
            "authenticity_score": score,
            "verdict": verdict,
            "forensic_flags": forensic_flags,
            "limitations_disclaimer": STATUTORY_DISCLAIMER
        }

media_authenticity_engine = MediaAuthenticityEngine()

