resource_types:
- name: docker-buildx
  type: docker-image
  privileged: true
  source:
    username: ((harbor.tools_token_username))
    password: ((harbor.tools_token))
    repository: harbor.finbourne.com/tools/docker-buildx
    tag: latest

resources:
- name: fbnconfig-image
  type: docker-buildx
  source:
    repository: harbor.finbourne.com/tools/fbnconfig
    docker_config_json: ((multi-registry.".dockerconfigjson"))
    username: ((harbor.tools_token_username))
    password: ((harbor.tools_token))