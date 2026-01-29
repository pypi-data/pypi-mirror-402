from abc import ABC

import alibabacloud_oss_v2 as oss
from alibabacloud_oss_v2 import GetObjectMetaRequest, GetObjectMetaResult, GetObjectRequest
from loguru import logger as log


class OssClient(ABC):
    def get_object_metadata(self, key: str):
        pass

    def get_object(self, key: str, target_path: str):
        pass

    def put_object(self, source_path: str, key: str):
        pass

    def delete_object(self, key: str):
        pass


class AliCloudOssClient(OssClient):
    _config: oss.Config
    _client: oss.Client
    _bucket: str

    def __init__(self, region: str, access_key: str, secret_key: str, endpoint: str, bucket: str):
        config = oss.config.load_default()
        config.region = region
        config.credentials_provider = oss.credentials.StaticCredentialsProvider(access_key_id=access_key,
                                                                                access_key_secret=secret_key)
        config.endpoint = endpoint
        self._config = config
        self.print_config()
        self._client = oss.Client(self._config)
        self._bucket = bucket

    def get_config(self) -> oss.Config:
        return self._config

    def get_object_metadata(self, key: str) -> GetObjectMetaResult:
        request = GetObjectMetaRequest(bucket=self._bucket, key=key)
        return self._client.get_object_meta(request)

    def get_object(self, key: str, target_path: str):
        log.debug(f"downloading {key} to {target_path}")
        request = GetObjectRequest(bucket=self._bucket, key=key)
        result = self._client.get_object(request)
        with result.body as body_stream:
            data = body_stream.read()
            with open(target_path, 'wb') as f:
                f.write(data)
        log.debug(f"finished downloading {key} to {target_path}")

    def put_object(self, source_path: str, key: str):
        pass

    def delete_object(self, key: str):
        pass

    def print_config(self):
        config_attrs = vars(self._config)
        config_str = "\n".join(f"{key}={value}" for key, value in config_attrs.items())
        log.debug(f"OSS Config: {config_str}")
