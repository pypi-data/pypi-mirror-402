#!/usr/bin/env python3

import argparse
import base64
import glob
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from importlib import import_module
from pathlib import Path
from typing import Any


def main() -> None:
    sys.path.insert(0, os.getcwd())

    parser = argparse.ArgumentParser(description="Sync API documentation to tech-docs repository")
    parser.add_argument("--fastapi-app", default="src.web.app", help="FastAPI app path")
    parser.add_argument("--faststream-app", default="src.messaging.app:app", help="FastStream app path")
    args = parser.parse_args()

    github_token = os.environ["GITHUB_TOKEN"]
    tech_docs_repo = os.environ["TECH_DOCS_REPO"]
    service_name = os.environ["SERVICE_NAME"]

    if openapi_docs := _generate_openapi_docs(args.fastapi_app):
        file_path = f"docs/services/{service_name}/openapi.json"

        _upload_json_to_github(
            repo=tech_docs_repo,
            file_path=file_path,
            content=openapi_docs,
            message=f"Update OpenAPI documentation for {service_name}",
            github_token=github_token,
        )

    if asyncapi_docs := _generate_asyncapi_docs(args.faststream_app):
        file_path = f"docs/services/{service_name}/asyncapi.json"

        _upload_json_to_github(
            repo=tech_docs_repo,
            file_path=file_path,
            content=asyncapi_docs,
            message=f"Update AsyncAPI documentation for {service_name}",
            github_token=github_token,
        )

    _sync_readme(tech_docs_repo, service_name, github_token)
    _sync_docs(tech_docs_repo, service_name, github_token)

    print(f"Docs of `{service_name}` service are synced successfully")


def _generate_openapi_docs(fastapi_app: str) -> dict | None:
    try:
        module_path, _, app_name = fastapi_app.partition(':')
        app_name = app_name or 'app'

        module = import_module(module_path)
        app = getattr(module, app_name)

        spec = app.openapi()

    except (ImportError, AttributeError) as e:
        print(f"Could not generate OpenAPI docs: {e}", file=sys.stderr)
        return None

    print("OpenAPI documentation generated")
    return spec


def _generate_asyncapi_docs(faststream_app: str) -> dict | None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = Path(temp_dir) / "asyncapi.json"

        exit_code = os.system(f"faststream docs gen {faststream_app} --out {output_file}")
        if exit_code != 0:
            print(f"Could not generate AsyncAPI docs", file=sys.stderr)
            return None

        with open(output_file, "r") as f:
            spec = json.load(f)

    print("AsyncAPI documentation generated")
    return spec


def _upload_json_to_github(
        repo: str,
        file_path: str,
        content: dict,
        message: str,
        github_token: str,
) -> None:
    _upload_file_to_github(repo, file_path, json.dumps(content), message, github_token)


def _sync_readme(repo: str, service_name: str, github_token: str) -> None:
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("README.md not found", file=sys.stderr)
        sys.exit(1)

    content = readme_path.read_text()
    file_path = f"docs/services/{service_name}/README.md"

    _upload_file_to_github(
        repo=repo,
        file_path=file_path,
        content=content,
        message=f"Update README for {service_name}",
        github_token=github_token,
    )


def _sync_docs(repo: str, service_name: str, github_token: str) -> None:
    docs_pattern = "docs/**/*.md"
    md_files = glob.glob(docs_pattern, recursive=True)

    for md_file in md_files:
        content = Path(md_file).read_text()
        file_path = f"docs/services/{service_name}/{md_file}"

        _upload_file_to_github(
            repo=repo,
            file_path=file_path,
            content=content,
            message=f"Update {md_file} for {service_name}",
            github_token=github_token,
        )


def _upload_file_to_github(
    repo: str,
    file_path: str,
    content: str,
    message: str,
    github_token: str,
) -> None:
    """Upload a text file to GitHub repository using the GitHub API."""

    new_content = base64.b64encode(content.encode("utf-8")).decode()
    old_file = _download_github_file(repo, file_path, github_token)
    if old_file:
        old_content = old_file["content"].replace("\n", "")
        if old_content == new_content:
            print(f"File {file_path} not changed. Skipping")
            return None

    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

    data = {
        "message": message,
        "content": new_content,
        "committer": {
            "name": "Zimran Documentation Bot",
            "email": "docs@zimran.io",
        },
    }

    if old_file:
        data["sha"] = old_file["sha"]

    json_data = json.dumps(data).encode()

    req = urllib.request.Request(url, data=json_data, method='PUT')
    req.add_header("Authorization", f"Bearer {github_token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as response:
            if response.status in (200, 201):
                print(f"Successfully uploaded {file_path}")
            else:
                print(f"Failed to upload {file_path}: {response.status}", file=sys.stderr)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"Failed to upload {file_path}: {e.code} - {error_body}", file=sys.stderr)


def _download_github_file(repo: str, file_path: str, github_token: str) -> dict[str, Any] | None:
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {github_token}")
    req.add_header("Accept", "application/vnd.github.v3+json")

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        else:
            raise Exception(f"Failed to get SHA for {file_path}: {e.code}")

    return data


if __name__ == "__main__":
    main()
