{{- define "git.branch" -}}
vnext
{{- end -}}

{{- define "version.file" -}}
fbnconfig-v02.version
{{- end -}}

{{- define "version.initial" -}}
0.2.0
{{- end -}}

{{- define "version.bump" -}}
pre: alpha
{{- end -}}

