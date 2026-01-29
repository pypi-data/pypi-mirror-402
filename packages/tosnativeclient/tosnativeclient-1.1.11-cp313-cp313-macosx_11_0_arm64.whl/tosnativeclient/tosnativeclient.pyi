from typing import List, Any, Tuple

from typing import Optional


def async_write_profile(seconds: int, file_path: str, image_width: int = 1200) -> None:
    ...


def init_tracing_log(directives: str = '', directory: str = '',
                     file_name_prefix: str = '') -> None:
    ...


class TosError(object):
    message: str
    status_code: Optional[int]
    ec: str
    request_id: str


class TosException(Exception):
    args: List[TosError]


class TosObject(object):
    bucket: str
    key: str
    size: int
    etag: str
    crc64: int


class ListObjectsResult(object):
    contents: List[TosObject]
    common_prefixes: List[str]


class ListStream(object):
    bucket: str
    prefix: str
    delimiter: str
    max_keys: int
    continuation_token: str
    start_after: str
    list_background_buffer_count: int
    prefetch: bool

    def __iter__(self) -> ListStream: ...

    def __next__(self) -> Optional[Tuple[ListObjectsResult, Optional[ReadStream]]]: ...

    def close(self) -> None: ...

    def current_prefix(self) -> Optional[str]: ...

    def current_continuation_token(self) -> Optional[str]: ...


class ReadStream(object):
    bucket: str
    key: str

    def read(self, offset: int, length: int) -> Optional[bytes]:
        ...

    def close(self) -> None:
        ...

    def is_closed(self) -> bool:
        ...

    def etag(self) -> str:
        ...

    def size(self) -> int:
        ...

    def crc64(self) -> int:
        ...

    def fetch_etag_size_err(self) -> Optional[str]:
        ...


class WriteStream(object):
    bucket: str
    key: str
    storage_class: Optional[str]

    def write(self, data: bytes) -> int:
        ...

    def close(self) -> None:
        ...

    def is_closed(self) -> bool:
        ...


class TosClient(object):
    region: str
    endpoint: str
    ak: str
    sk: str
    part_size: int
    max_retry_count: int
    max_prefetch_tasks: int
    shared_prefetch_tasks: int
    enable_crc: bool
    max_upload_part_tasks: int
    shared_upload_part_tasks: int

    def __init__(self, region: str, endpoint: str, ak: str = '', sk: str = '', part_size: int = 8388608,
                 max_retry_count: int = 3, max_prefetch_tasks: int = 3, shared_prefetch_tasks: int = 32,
                 enable_crc: bool = True, max_upload_part_tasks: int = 3, shared_upload_part_tasks: int = 32,
                 dns_cache_async_refresh: bool = False, use_global_runtime:bool=False):
        ...

    def list_objects(self, bucket: str, prefix: str = '', max_keys: int = 1000, delimiter: str = '',
                     continuation_token: str = '', start_after: str = '',
                     list_background_buffer_count: int = 1, prefetch_concurrency: int = 0,
                     distributed_info: Optional[Tuple[int, int, int, int]] = None) -> ListStream:
        ...

    def head_object(self, bucket: str, key: str) -> TosObject:
        ...

    def batch_get_objects(self, objects: List[Tuple[str, str, Optional[str], Optional[int], Optional[int]]],
                          prefetch_concurrency: int = 0, fetch_etag_size: bool = False) -> List[
        ReadStream]:
        ...

    def get_object(self, bucket: str, key: str, etag: Optional[str] = None, size: Optional[int] = None,
                   crc64: Optional[int] = None, preload: bool = False) -> ReadStream:
        ...

    def put_object(self, bucket: str, key: str, storage_class: Optional[str] = '') -> WriteStream:
        ...

    def close(self) -> None:
        ...
