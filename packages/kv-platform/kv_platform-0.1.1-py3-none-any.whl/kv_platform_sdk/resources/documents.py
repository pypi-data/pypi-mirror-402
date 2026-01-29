from pathlib import Path
from typing import Any, Dict, List



class DocumentsResource:
    def __init__(self, http_client):
        self._http = http_client

    def list(self):
        response = self._http.get("/api/doc/get_all")
        return response

    def process_file(self, file_path: str):
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "rb") as f:
            files = {"file": (path.name, f)}
            response = self._http.post(
                "/api/doc/process_doc",
                files=files,
            )

        return response

    def process_s3(
        self,
        *,
        s3_uri: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
    ):
        payload = {
            "s3_uri": s3_uri,
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_region": aws_region,
        }

        response = self._http.post(
            "/api/doc/process_doc",
            json=payload,
            headers={"Content-Type": "application/json"},
        )

        return response

    def delete(self, doc_process_ids: List[str]):
        response = self._http.delete(
            "/api/doc/delete",
            json={"doc_process_ids": doc_process_ids},
            headers={"Content-Type": "application/json"},
        )
        return response


class AsyncDocumentsResource:
    def __init__(self, http_client):
        self._http = http_client

    async def list(self):
        response = await self._http.get("/api/doc/get_all")
        return response

    async def process_file(self, file_path: str):
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "rb") as f:
            files = {"file": (path.name, f)}
            response = await self._http.post(
                "/api/doc/process_doc",
                files=files,
            )

        return response

    async def process_s3(
        self,
        *,
        s3_uri: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
    ):
        payload = {
            "s3_uri": s3_uri,
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_region": aws_region,
        }

        response = await self._http.post(
            "/api/doc/process_doc",
            json=payload,
            headers={"Content-Type": "application/json"},
        )

        return response

    async def delete(self, doc_process_ids: List[str]):
        response = await self._http.delete(
            "/api/doc/delete",
            json={"doc_process_ids": doc_process_ids},
            headers={"Content-Type": "application/json"},
        )
        return response
