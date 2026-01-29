groups:
  - name: build-and-test
    jobs:
      - merge-request
      - build
      - build-image
      - run-examples
      - publish-to-pypi
      - mirror-examples
  - name: bump-versions
    jobs:
      - bump-version-minor
      - bump-version-major

merge:
  - template: pipelines/merge-request.tpl
  - template: pipelines/build.tpl
  - template: pipelines/build-image.tpl
  - template: pipelines/run-examples.tpl
  - template: pipelines/publish-to-pypi.tpl
  - template: pipelines/mirror-examples.tpl
  - template: pipelines/bump-version-minor.tpl
  - template: pipelines/bump-version-major.tpl
  - template: resources/fbnconfig-image.tpl

