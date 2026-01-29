resources:
  - name: source-code-fbnconfig
    type: git
    icon: gitlab
    source:
      uri: git@gitlab.com:finbourne/clientengineering/fbnconfig.git
      branch: {{ template "git.branch" }}
      private_key: ((gitlab.id_rsa))
