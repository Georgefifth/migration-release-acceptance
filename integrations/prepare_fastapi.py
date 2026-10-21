"""Fetch only a fixed public source revision; preserve its MIT license and lock."""
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

SHA = 'b1125d8839482cb7bbae603ddc6d0081bf87532e'
MODEL_BLOB = '181acf2bf16b4285becb5a5626cf3aa56210211e'
ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / '.upstream'
SOURCE = BASE / 'source'


def patch_models(text):
    original_line = '    title: str = Field(min_length=1, max_length=255)'
    if text.count(original_line) != 1:
        raise RuntimeError('Expected one reviewed ItemBase field')
    text = text.replace('from sqlmodel import', 'from sqlalchemy import Column, String\nfrom sqlmodel import', 1)
    text = text.replace(original_line, '    title: str = Field(min_length=1, max_length=255, sa_column=Column("display_title", String(255), nullable=False))')
    return text


def main():
    BASE.mkdir(exist_ok=True)
    if SOURCE.exists():
        raise RuntimeError('Use a fresh checkout; do not overwrite an existing upstream tree')
    archive = BASE / 'fastapi.zip'
    with urllib.request.urlopen(
            f'https://codeload.github.com/fastapi/full-stack-fastapi-template/zip/{SHA}', timeout=60) as response:
        archive.write_bytes(response.read())
    with zipfile.ZipFile(archive) as package:
        # Source comes from the public official repository; still reject path traversal.
        for item in package.infolist():
            if not (BASE / item.filename).resolve().is_relative_to(BASE.resolve()):
                raise ValueError('Invalid archive path')
        package.extractall(BASE)
    (BASE / f'full-stack-fastapi-template-{SHA}').rename(SOURCE)
    original = (SOURCE / 'backend/app/models.py').read_bytes()
    digest = hashlib.sha1(f'blob {len(original)}\0'.encode() + original).hexdigest()
    if digest != MODEL_BLOB:
        raise RuntimeError('Pinned model blob mismatch')
    for version in ['v1', 'v2']:
        target = BASE / version / 'app'
        shutil.copytree(SOURCE / 'backend/app', target)
        # Upstream serves a built frontend; our case only exercises its backend.
        (target / 'frontend').mkdir(exist_ok=True)
        (target / 'frontend/index.html').write_text('<!doctype html><title>Backend acceptance fixture</title>')
    model = BASE / 'v2/app/models.py'
    text = patch_models(model.read_text())
    model.write_text(text)
    manifest = dict(repository='fastapi/full-stack-fastapi-template', commit=SHA,
                    original_model_blob=MODEL_BLOB,
                    patched_model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
                    lock_sha256=hashlib.sha256((SOURCE / 'uv.lock').read_bytes()).hexdigest(),
                    change='v2 Item.title maps to physical column display_title; API title stays unchanged')
    (BASE / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
