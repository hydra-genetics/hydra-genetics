on:
  workflow_dispatch:

name: test-build-pip-package

jobs:
  test-build-pip-package:
    runs-on: ubuntu-latest
    steps:
      - uses: GoogleCloudPlatform/release-please-action@v2
        id: release
        with:
          release-type: python
          package-name: hydra-genetics
          default-branch: master

      - uses: actions/checkout@v2
        if: ${{ steps.release.outputs.release_created }}
        with:
          fetch-depth: 0

      - name: Set up Python
        if: ${{ steps.release.outputs.release_created }}
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'

      - name: Build package
        if: ${{ steps.release.outputs.release_created }}
        run: |
          python -m pip install --upgrade pip
          python setup.py sdist
