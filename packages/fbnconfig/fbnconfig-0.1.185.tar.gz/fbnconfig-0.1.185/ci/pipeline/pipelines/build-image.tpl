jobs:
- name: build-image
  plan:
  - in_parallel:
    - get: source-code-fbnconfig
      trigger: true
      passed: [build]
    - get: fbnconfig-version
      trigger: true
      passed: [build]
  
  - put: fbnconfig-image
    params:
      docker_buildkit: 1
      build: source-code-fbnconfig
      tag: fbnconfig-version/version
      tag_as_latest: true