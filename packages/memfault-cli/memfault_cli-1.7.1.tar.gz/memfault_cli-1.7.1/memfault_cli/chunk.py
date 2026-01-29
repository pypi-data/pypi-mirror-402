import math
import os
import re
from base64 import b64decode
from typing import List

import requests.utils
import tqdm
from more_itertools import chunked
from requests import PreparedRequest

from .authenticator import Authenticator
from .context import MemfaultCliClickContext

EXPORTED_CHUNKS_REGEX = re.compile(r"MC:([a-zA-z0-9+/=]+):")


class MemfaultChunk:
    def __init__(self, ctx: MemfaultCliClickContext, authenticator: Authenticator):
        self.ctx = ctx
        self.authenticator = authenticator

    @property
    def url(self):
        return f"{self.ctx.chunks_url}/api/v0/chunks/{self.ctx.device_serial}"

    def post(self, chunk: bytes):
        request_args = self.authenticator.requests_auth_params()
        request_args["headers"]["Content-Type"] = "application/octet-stream"
        response = requests.post(self.url, data=chunk, **request_args)
        if response.status_code >= 400:
            raise RuntimeError(
                f"Request failed with HTTP status {response.status_code}\nResponse"
                f" body:\n{response.content.decode()}"
            )

    def do_batch_post(self, files: List):
        """Issue a post with a batch of files (HTTP Multipart)"""
        request_args = self.authenticator.requests_auth_params()

        # Pick up default headers and merge with Memfault Auth headers
        headers = requests.utils.default_headers()
        headers.update(request_args["headers"])
        del request_args["headers"]

        request = PreparedRequest()
        request.prepare(method="POST", url=self.url, files=files, headers=headers, **request_args)
        content_type: str = request.headers["content-type"]
        request.headers["content-type"] = content_type.replace("form-data", "mixed")

        session = requests.Session()
        response = session.send(request)
        if response.status_code >= 400:
            raise RuntimeError(
                f"Request failed with HTTP status {response.status_code}\nResponse"
                f" body:\n{response.content.decode()}"
            )

    def batch_post(self, chunks: List[bytes]):
        """
        Post a batch of chunks to the Memfault Chunk API. Will break the request
        into multiple Multipart requests if the chunk count is too large
        """
        if len(chunks) == 1:
            self.post(chunks[0])
            return

        files = []
        for idx, chunk in enumerate(chunks):
            files.append((
                # "Content-Disposition" header
                f"chunk{idx}",
                # (filename, fileobj, contentype, custom_headers)
                (
                    f"chunk.bin{idx}",
                    chunk,
                    "application/octet-stream",
                    {"Content-Length": len(chunk)},
                ),
            ))

        # by default, limit each request to 500 chunks. this is an extreme edge
        # case but it can happen.
        batch_size = int(os.environ.get("MEMFAULT_CLI_CHUNK_BATCH_SIZE", "500"))

        if len(files) <= batch_size:
            # do a single post if the chunk count is small enough
            self.do_batch_post(files)
        else:
            # otherwise, break the request into multiple posts
            for chunk_group in tqdm.tqdm(
                chunked(files, batch_size),
                total=math.ceil(len(files) / batch_size),
                unit="batch",
                desc=f"Uploading chunks in batches of {batch_size}",
            ):
                self.do_batch_post(chunk_group)

    @staticmethod
    def extract_exported_chunks(data: str):
        chunks = []
        for match in EXPORTED_CHUNKS_REGEX.finditer(data):
            binary_encoded_chunk = b64decode(match.group(1))
            chunks.append(binary_encoded_chunk)
        return chunks
