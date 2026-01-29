"""Unit tests for infinity_ml models."""

import pytest

from infinity_ml.models import (
    AudioResult,
    Completed,
    Failed,
    ImageResult,
    InProgress,
    Queued,
    VideoResult,
    parse_result,
    parse_status,
)


class TestParseStatus:
    """Tests for parse_status function."""

    def test_parse_queued(self):
        data = {"status": "IN_QUEUE", "queue_position": 3}
        status = parse_status(data)
        assert isinstance(status, Queued)
        assert status.position == 3

    def test_parse_queued_default_position(self):
        data = {"status": "IN_QUEUE"}
        status = parse_status(data)
        assert isinstance(status, Queued)
        assert status.position == 0

    def test_parse_in_progress(self):
        data = {"status": "IN_PROGRESS", "logs": [{"message": "Processing"}]}
        status = parse_status(data)
        assert isinstance(status, InProgress)
        assert status.logs == [{"message": "Processing"}]

    def test_parse_completed(self):
        data = {"status": "COMPLETED", "metrics": {"duration_ms": 1500}}
        status = parse_status(data)
        assert isinstance(status, Completed)
        assert status.metrics == {"duration_ms": 1500}

    def test_parse_failed(self):
        data = {"status": "FAILED", "error": "Out of memory"}
        status = parse_status(data)
        assert isinstance(status, Failed)
        assert status.error == "Out of memory"

    def test_parse_unknown_status(self):
        data = {"status": "UNKNOWN"}
        status = parse_status(data)
        # Returns base Status for unknown
        assert type(status).__name__ == "Status"


class TestParseResult:
    """Tests for parse_result function."""

    def test_parse_image_result(self):
        data = {
            "images": [
                {
                    "url": "/files/image.png",
                    "download_url": "https://example.com/files/image.png",
                    "content_type": "image/png",
                    "width": 1024,
                    "height": 768,
                }
            ],
            "seed": 42,
            "prompt": "A cat",
        }
        result = parse_result(data, "req-123")
        assert isinstance(result, ImageResult)
        assert len(result.images) == 1
        assert result.images[0].width == 1024
        assert result.images[0].height == 768
        assert result.seed == 42
        assert result.prompt == "A cat"
        assert result.request_id == "req-123"

    def test_parse_video_result(self):
        data = {
            "video": {
                "url": "/files/video.mp4",
                "download_url": "https://example.com/files/video.mp4",
                "content_type": "video/mp4",
                "width": 1280,
                "height": 720,
                "duration": 5.0,
            },
            "seed": 123,
            "prompt": "Ocean waves",
        }
        result = parse_result(data, "req-456")
        assert isinstance(result, VideoResult)
        assert result.video.width == 1280
        assert result.video.duration == 5.0
        assert result.seed == 123
        assert result.request_id == "req-456"

    def test_parse_audio_result(self):
        data = {
            "audio": {
                "url": "/files/audio.wav",
                "download_url": "https://example.com/files/audio.wav",
                "content_type": "audio/wav",
                "duration": 3.5,
            },
        }
        result = parse_result(data, "req-789")
        assert isinstance(result, AudioResult)
        assert result.audio.duration == 3.5
        assert result.request_id == "req-789"

    def test_parse_unknown_result_raises(self):
        data = {"unknown_field": "value"}
        with pytest.raises(ValueError, match="Unknown result type"):
            parse_result(data, "req-000")


class TestStatusDataclasses:
    """Tests for status dataclass fields."""

    def test_queued_defaults(self):
        q = Queued()
        assert q.position == 0

    def test_in_progress_defaults(self):
        ip = InProgress()
        assert ip.logs is None

    def test_completed_defaults(self):
        c = Completed()
        assert c.logs is None
        assert c.metrics == {}

    def test_failed_defaults(self):
        f = Failed()
        assert f.error == ""
