"""
Transcoding and encoder preset constants.
"""

AUDIO_CODEC = "aac"
AUDIO_BITRATE = "128k"

TRANSCODE_COMMON_ARGS = [
    "-movflags", "+faststart",
    "-avoid_negative_ts", "make_zero"
]

DOWNLOAD_PRESETS = [
    "Best Quality",
    "2160p",
    "1440p",
    "1080p",
    "720p",
    "480p",
    "360p",
    "Audio (wav)",
    "Audio (mp3)",
    "Audio (m4a)",
    "Audio (flac)"
]

ENCODER_OPTIONS = [
    "Auto",
    "H.264 (Nvidia)",
    "H.265 (Nvidia)",
    "AV1 (Nvidia)",
    "H.264 (AMD)",
    "H.265 (AMD)",
    "AV1 (AMD)",
    "H.264 (Intel QuickSync)",
    "H.265 (Intel QuickSync)",
    "AV1 (Intel QuickSync)",
    "H.264 (CPU)",
    "AV1 (CPU)"
]

ENCODER_MAPPING = {
    "Auto": None,
    "H.264 (Nvidia)": {
        "encoder": "h264_nvenc",
        "name": "NVIDIA NVENC H.264",
        "hwaccel": "cuda",
        "codec": "h264",
        "settings": {"preset": "p4", "rc": "vbr", "cq": "23", "b:v": "0"}
    },
    "H.265 (Nvidia)": {
        "encoder": "hevc_nvenc",
        "name": "NVIDIA NVENC H.265",
        "hwaccel": "cuda",
        "codec": "h265",
        "settings": {"preset": "p4", "rc": "vbr", "cq": "25", "b:v": "0"}
    },
    "H.264 (AMD)": {
        "encoder": "h264_amf",
        "name": "AMD AMF H.264",
        "hwaccel": None,
        "codec": "h264",
        "settings": {"quality": "balanced", "rc": "vbr_peak", "qp_i": "22", "qp_p": "24"}
    },
    "H.265 (AMD)": {
        "encoder": "hevc_amf",
        "name": "AMD AMF H.265",
        "hwaccel": None,
        "codec": "h265",
        "settings": {"quality": "balanced", "rc": "vbr_peak", "qp_i": "24", "qp_p": "26"}
    },
    "H.264 (Intel QuickSync)": {
        "encoder": "h264_qsv",
        "name": "Intel QuickSync H.264",
        "hwaccel": None,
        "codec": "h264",
        "settings": {"preset": "medium", "global_quality": "23"}
    },
    "H.265 (Intel QuickSync)": {
        "encoder": "hevc_qsv",
        "name": "Intel QuickSync H.265",
        "hwaccel": None,
        "codec": "h265",
        "settings": {"preset": "medium", "global_quality": "25"}
    },
    "H.264 (CPU)": {
        "encoder": "libx264",
        "name": "CPU Software H.264",
        "hwaccel": None,
        "codec": "h264",
        "settings": {"preset": "medium", "crf": "23"}
    },
    "AV1 (Nvidia)": {
        "encoder": "av1_nvenc",
        "name": "NVIDIA NVENC AV1",
        "hwaccel": "cuda",
        "codec": "av1",
        "settings": {"preset": "p4", "rc": "vbr", "cq": "35", "b:v": "0"}
    },
    "AV1 (AMD)": {
        "encoder": "av1_amf",
        "name": "AMD AMF AV1",
        "hwaccel": None,
        "codec": "av1",
        "settings": {"quality": "balanced", "rc": "cqp", "qp_i": "28", "qp_p": "28"}
    },
    "AV1 (Intel QuickSync)": {
        "encoder": "av1_qsv",
        "name": "Intel QuickSync AV1",
        "hwaccel": None,
        "codec": "av1",
        "settings": {"preset": "medium", "global_quality": "28"}
    },
    "AV1 (CPU)": {
        "encoder": "libsvtav1",
        "name": "SVT-AV1 (CPU)",
        "hwaccel": None,
        "codec": "av1",
        "settings": {"crf": "35", "preset": "8"}
    }
}

CODEC_CPU_FALLBACK = {
    "h264": "H.264 (CPU)",
    "h265": "H.264 (CPU)",
    "av1": "AV1 (CPU)",
}

ENCODER_PROGRESS_MESSAGES = {
    "H.264 (Nvidia)": "Encoding to H.264 (NVIDIA NVENC H.264)",
    "H.265 (Nvidia)": "Encoding to H.265 (NVIDIA NVENC HEVC)",
    "AV1 (Nvidia)": "Encoding to AV1 (NVIDIA NVENC AV1)",
    "H.264 (AMD)": "Encoding to H.264 (AMD AMF H.264)",
    "H.265 (AMD)": "Encoding to H.265 (AMD AMF HEVC)",
    "AV1 (AMD)": "Encoding to AV1 (AMD AMF AV1)",
    "H.264 (Intel QuickSync)": "Encoding to H.264 (QuickSync H.264)",
    "H.265 (Intel QuickSync)": "Encoding to H.265 (QuickSync HEVC)",
    "AV1 (Intel QuickSync)": "Encoding to AV1 (QuickSync AV1)",
    "H.264 (CPU)": "Encoding to H.264 (CPU x264)",
    "AV1 (CPU)": "Encoding to AV1 (SVT-AV1)"
}

ENCODERS_CONFIG = [
    {
        "encoder": "h264_nvenc",
        "name": "NVIDIA NVENC",
        "hwaccel": "cuda",
        "test_args": ["-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-t", "1"],
        "settings": {"preset": "p4", "rc": "vbr", "cq": "23", "b:v": "0"}
    },
    {
        "encoder": "h264_amf",
        "name": "AMD AMF",
        "hwaccel": "d3d11va",
        "test_args": ["-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-t", "1"],
        "settings": {"quality": "balanced", "rc": "cqp", "qp_i": "23", "qp_p": "23", "qp_b": "23"}
    },
    {
        "encoder": "h264_qsv",
        "name": "Intel Quick Sync",
        "hwaccel": None,
        "test_args": ["-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-t", "1"],
        "settings": {"preset": "medium", "global_quality": "23"}
    },
    {
        "encoder": "libx264",
        "name": "CPU (Software)",
        "hwaccel": None,
        "test_args": ["-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-t", "1"],
        "settings": {"preset": "medium", "crf": "23"}
    }
]
