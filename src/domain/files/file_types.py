from enum import Enum


class FileType(str, Enum):
    THUMBNAIL = 'thumbnail',
    FEATURED = 'featured',
    CONTENT = 'content',
    GALLERY = 'gallery',
    DOCUMENT = 'document',
    VIDEO = 'video',
    AUDIO = 'audio',
    OTHER = 'other',