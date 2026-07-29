"""
UI strings and messages.
"""
from app.utils.localization import _

class MessagesMeta(type):
    @property
    def URL_EMPTY(cls):
        return _("errors.url_empty")

    @property
    def GETTING_INFO(cls):
        return _("status.getting_info")

    @property
    def READY_DOWNLOAD(cls):
        return _("status.ready_download")

    @property
    def DOWNLOADING(cls):
        return _("status.downloading")

    @property
    def DOWNLOAD_COMPLETE(cls):
        return _("status.download_complete")

    @property
    def DOWNLOAD_CANCELLED(cls):
        return _("status.download_cancelled")

    @property
    def DOWNLOAD_INTERRUPTED(cls):
        return _("status.download_interrupted")

    @property
    def DOWNLOAD_FAILED(cls):
        return _("status.download_failed")

    @property
    def TIMEOUT_ANALYZE(cls):
        return _("errors.timeout_analyze")

    @property
    def VIDEO_UNAVAILABLE(cls):
        return _("errors.video_unavailable")

    @property
    def VIDEO_NOT_FOUND(cls):
        return _("errors.video_not_found")

    @property
    def AGE_RESTRICTED(cls):
        return _("errors.age_restricted")

    @property
    def FAILED_VIDEO_INFO(cls):
        return _("errors.failed_video_info")

    @property
    def INVALID_URL(cls):
        return _("errors.invalid_url")

    @property
    def DOWNLOAD_FORBIDDEN(cls):
        return _("errors.download_forbidden")

    @property
    def COOKIE_EXTRACTION_FAILED(cls):
        return _("errors.cookie_extraction_failed")

    @property
    def ENCODING_FAILED(cls):
        return _("errors.encoding_failed")

    @property
    def FILE_NOT_FOUND(cls):
        return _("errors.file_not_found")

    @property
    def ENCODING_ERROR(cls):
        return _("errors.encoding_error")

    @property
    def FILE_MOVE_ERROR(cls):
        return _("errors.file_move_error")

class Messages(metaclass=MessagesMeta):
    pass
