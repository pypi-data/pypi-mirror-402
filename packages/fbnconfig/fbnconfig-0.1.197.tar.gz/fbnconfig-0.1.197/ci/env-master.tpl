{{- define "git.branch" -}}
master
{{- end -}}

{{- define "version.file" -}}
fbnconfig.version
{{- end -}}

{{- define "version.initial" -}}
0.0.1
{{- end -}}

{{- define "version.bump" -}}
bump: patch
{{- end -}}

