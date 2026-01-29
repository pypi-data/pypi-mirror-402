merge:
  - template: resource_types/semver.tpl

resources:
  - name: fbnconfig-version
    type: semver
    icon: exponent
    source:
      driver: git
      branch: master
      uri: git@gitlab.com:finbourne/cicd/versions.git
      file: {{ template "version.file" }}
      initial_version: {{ template "version.initial" }}
      private_key: ((gitlab.id_rsa))
