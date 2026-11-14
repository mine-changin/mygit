"""CKA / CKAD 학습노트 (치트시트). 항목을 추가하려면 NOTES 에 dict 를 더하면 됩니다.
필드: id, title, exams(["CKA","CKAD"]), cat(카테고리), tags(검색 동의어/키워드), body(마크다운)
※ 시험 커리큘럼·쿠버네티스 버전은 바뀔 수 있으므로 CNCF 공식 커리큘럼과 kubernetes.io 문서로 최종 확인하세요."""

CATS = ["시험 팁", "아키텍처·설치", "워크로드·스케줄링", "서비스·네트워킹", "스토리지",
        "구성·보안", "배포·릴리스", "관찰·디버깅", "트러블슈팅"]

# 도메인별 시험 비중 (공식 커리큘럼 기준, 변경 가능)
EXAMS = {
    "CKA": {"name": "Certified Kubernetes Administrator",
            "domains": [("트러블슈팅", 30), ("클러스터 아키텍처·설치·구성", 25), ("서비스·네트워킹", 20),
                        ("워크로드·스케줄링", 15), ("스토리지", 10)]},
    "CKAD": {"name": "Certified Kubernetes Application Developer",
             "domains": [("환경·구성·보안", 25), ("애플리케이션 설계·빌드", 20), ("애플리케이션 배포", 20),
                         ("서비스·네트워킹", 20), ("관찰·유지보수", 15)]},
}

NOTES = [
# ------------------------------------------------------------------ 시험 팁
dict(id="exam-overview", title="시험 개요와 시간 전략", exams=["CKA", "CKAD"], cat="시험 팁",
     tags=["시험", "합격", "점수", "시간", "전략", "문서", "북마크", "exam", "strategy"],
     body="""# 형식
- 온라인 감독(PSI) **실습형** 시험, 제한시간 **2시간**, 합격선 **66%**
- 허용 자료: kubernetes.io/docs, helm 문서 등 **공식 문서 일부** (북마크 가능). 그 외 검색 불가
# 전략
1. 문제마다 가중치(%)가 다르다 → **쉬운 문제·가중치 높은 문제부터**, 막히면 flag 후 넘어가기
2. **매 문제 시작 시 컨텍스트 전환 명령을 복사해 실행** (클러스터가 문제마다 다름)
3. 작업 후 반드시 `kubectl get`/`describe` 로 결과 검증
4. YAML 은 직접 타이핑하지 말고 `--dry-run=client -o yaml` 로 생성 후 수정
5. 남은 시간 15분은 flag 한 문제 재시도에 사용
# 준비
- killer.sh 모의고사(등록 시 2회 제공)를 시험 1주 전에 풀어보기
- 매 학습 때 `kubectl explain`, 공식 문서 검색 속도를 훈련"""),

dict(id="exam-env", title="시험 환경 세팅 (alias · vim · 자동완성)", exams=["CKA", "CKAD"], cat="시험 팁",
     tags=["alias", "vim", "bashrc", "completion", "자동완성", "단축", "환경설정", "dry-run"],
     body="""시험 시작 직후 1~2분 투자해 세팅한다. (이미 alias `k` 가 설정된 경우도 있으니 확인)
```
alias k=kubectl
source <(kubectl completion bash)
complete -o default -F __start_kubectl k
export do="--dry-run=client -o yaml"
export now="--force --grace-period 0"
```
```
# ~/.vimrc  (YAML 들여쓰기)
set tabstop=2 shiftwidth=2 expandtab
```
사용 예: `k run web --image=nginx $do > pod.yaml`, `k delete pod web $now`
- 컨텍스트/네임스페이스: `k config use-context <ctx>`, `k config set-context --current --namespace=dev`"""),

dict(id="kubectl-gen", title="YAML 빠르게 생성 (imperative 명령)", exams=["CKA", "CKAD"], cat="시험 팁",
     tags=["run", "create", "expose", "dry-run", "yaml", "imperative", "생성", "명령형"],
     body="""```
k run nginx --image=nginx --port=80 --labels=app=web $do
k run tmp --rm -it --image=busybox:1.36 --restart=Never -- sh
k create deploy web --image=nginx --replicas=3 $do
k expose deploy web --port=80 --target-port=8080 --type=NodePort
k create job j1 --image=busybox -- echo hi
k create cronjob c1 --image=busybox --schedule="*/5 * * * *" -- date
k create cm app-cfg --from-literal=k=v --from-file=app.conf
k create secret generic db --from-literal=password=s3cr3t
k create sa build-sa
k create role r --verb=get,list --resource=pods
k create rolebinding rb --role=r --user=jane
k create ingress ing --rule="foo.com/bar*=svc1:8080" $do
k autoscale deploy web --min=2 --max=10 --cpu-percent=50
```
- DaemonSet 은 `create` 명령이 없다 → `create deploy ... $do` 로 만든 뒤 `kind: DaemonSet`, `replicas`/`strategy` 제거
- 컨테이너 명령: `k run x --image=busybox $do -- sleep 3600` (`--` 뒤가 command/args)"""),

dict(id="kubectl-output", title="출력 가공: jsonpath · custom-columns · sort-by", exams=["CKA", "CKAD"], cat="시험 팁",
     tags=["jsonpath", "custom-columns", "sort-by", "selector", "field-selector", "explain", "출력", "정렬"],
     body="""```
k get nodes -o jsonpath='{.items[*].metadata.name}'
k get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\\t"}{.status.podIP}{"\\n"}{end}'
k get pods -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[*].image
k get pods --sort-by=.metadata.creationTimestamp
k get pv --sort-by=.spec.capacity.storage
k get pods -A --field-selector spec.nodeName=node01
k get pods -l app=web,tier=front
k get events --sort-by=.metadata.creationTimestamp
k explain pod.spec.containers.securityContext --recursive
k api-resources --namespaced=false
```
- 필드 위치를 모를 때 `k explain <resource>.<path>` 가 문서 검색보다 빠르다"""),

# ------------------------------------------------------------------ 아키텍처·설치
dict(id="etcd-backup", title="etcd 백업 / 복구", exams=["CKA"], cat="아키텍처·설치",
     tags=["etcd", "snapshot", "backup", "restore", "백업", "복구", "etcdctl", "etcdutl"],
     body="""# 백업
```
ETCDCTL_API=3 etcdctl snapshot save /opt/etcd-backup.db \\
  --endpoints=https://127.0.0.1:2379 \\
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \\
  --cert=/etc/kubernetes/pki/etcd/server.crt \\
  --key=/etc/kubernetes/pki/etcd/server.key
etcdctl snapshot status /opt/etcd-backup.db -w table
```
- 인증서 경로 확인: `cat /etc/kubernetes/manifests/etcd.yaml | grep -E 'cert|key|trusted|listen-client'`
# 복구
```
etcdutl snapshot restore /opt/etcd-backup.db --data-dir /var/lib/etcd-restore
# (구버전: etcdctl snapshot restore ...)
```
1. `/etc/kubernetes/manifests/etcd.yaml` 의 volume `etcd-data` hostPath 를 `/var/lib/etcd-restore` 로 변경
2. kubelet 이 static pod 를 재생성할 때까지 대기 (`crictl ps | grep etcd`)
3. `kubectl get nodes,pods -A` 로 데이터 복구 확인"""),

dict(id="kubeadm-upgrade", title="kubeadm 클러스터 업그레이드", exams=["CKA"], cat="아키텍처·설치",
     tags=["kubeadm", "upgrade", "업그레이드", "drain", "kubelet", "apt", "버전"],
     body="""마이너 버전은 **한 단계씩**만 올린다 (1.30 → 1.31).
# 컨트롤 플레인
```
apt-mark unhold kubeadm && apt-get update
apt-get install -y kubeadm=1.31.x-*  && apt-mark hold kubeadm
kubeadm upgrade plan
kubeadm upgrade apply v1.31.x
kubectl drain <cp-node> --ignore-daemonsets
apt-get install -y kubelet=1.31.x-* kubectl=1.31.x-*
systemctl daemon-reload && systemctl restart kubelet
kubectl uncordon <cp-node>
```
# 워커 노드
```
(컨트롤 플레인에서) kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
(워커에서)  apt-get install -y kubeadm=1.31.x-*
            kubeadm upgrade node
            apt-get install -y kubelet=1.31.x-* ; systemctl daemon-reload ; systemctl restart kubelet
(컨트롤 플레인에서) kubectl uncordon <node>
```"""),

dict(id="kubeadm-join", title="kubeadm 초기화 · 노드 조인 · 토큰", exams=["CKA"], cat="아키텍처·설치",
     tags=["kubeadm", "join", "init", "token", "조인", "초기화", "cni", "설치"],
     body="""```
kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=<IP>
mkdir -p $HOME/.kube && cp /etc/kubernetes/admin.conf $HOME/.kube/config
kubectl apply -f <CNI manifest>          # 설치 후 노드가 Ready
kubeadm token create --print-join-command   # 워커 조인 명령 재생성
```
- 사전 조건: swap off, containerd 기동, `br_netfilter` 모듈 및 `net.ipv4.ip_forward=1`
- 토큰은 기본 24시간 후 만료 → 위 명령으로 재발급
- 노드가 NotReady 로 남으면 CNI 미설치/kubelet 오류 확인"""),

dict(id="node-maint", title="노드 관리: cordon · drain · taint", exams=["CKA"], cat="아키텍처·설치",
     tags=["drain", "cordon", "uncordon", "노드", "유지보수", "evict", "스케줄"],
     body="""```
k cordon node01                       # 새 파드 스케줄만 차단
k drain node01 --ignore-daemonsets --delete-emptydir-data   # 파드 축출 + cordon
k uncordon node01
k get nodes -o wide
```
- drain 이 막히는 경우: 단독 파드(컨트롤러 없음) → `--force`, PDB 위반, DaemonSet → `--ignore-daemonsets`
- 노드 레이블: `k label node node01 disk=ssd` / 제거 `k label node node01 disk-`"""),

dict(id="rbac", title="RBAC: Role · ClusterRole · Binding", exams=["CKA", "CKAD"], cat="구성·보안",
     tags=["rbac", "role", "rolebinding", "clusterrole", "serviceaccount", "can-i", "권한", "인가"],
     body="""```
k create role pod-reader --verb=get,list,watch --resource=pods -n dev
k create rolebinding rb-jane --role=pod-reader --user=jane -n dev
k create clusterrole node-reader --verb=get,list --resource=nodes
k create clusterrolebinding crb --clusterrole=node-reader --user=jane
k create rolebinding sa-rb --role=pod-reader --serviceaccount=dev:build-sa -n dev
k auth can-i list pods -n dev --as jane
k auth can-i --list --as system:serviceaccount:dev:build-sa -n dev
```
- Role/RoleBinding 은 **네임스페이스 범위**, ClusterRole/ClusterRoleBinding 은 클러스터 범위
- ClusterRole 을 RoleBinding 으로 묶으면 해당 네임스페이스에만 적용
- `Forbidden` 에러 → 메시지의 verb/resource/namespace 를 그대로 Role 에 추가"""),

dict(id="crd-helm-kustomize", title="Helm · Kustomize · CRD", exams=["CKA", "CKAD"], cat="배포·릴리스",
     tags=["helm", "kustomize", "crd", "operator", "chart", "overlay", "patch", "차트"],
     body="""# Helm
```
helm repo add bitnami https://charts.bitnami.com/bitnami && helm repo update
helm search repo nginx
helm install my-web bitnami/nginx -n web --create-namespace --set replicaCount=2
helm upgrade my-web bitnami/nginx -f values.yaml
helm rollback my-web 1
helm list -A ; helm uninstall my-web -n web
helm template my-web bitnami/nginx > out.yaml
helm get values my-web
```
# Kustomize
```
# kustomization.yaml
resources: [deployment.yaml, service.yaml]
namePrefix: dev-
namespace: dev
images:
- name: nginx
  newTag: "1.27"
patches:
- path: patch.yaml
```
`k kustomize ./dir` (미리보기), `k apply -k ./dir`
# CRD
`k get crd`, `k explain <kind>`, `k get <plural> -A` — CR 은 CRD 의 plural/shortName 으로 조회"""),

# ------------------------------------------------------------------ 워크로드·스케줄링
dict(id="deploy-rollout", title="Deployment 롤링업데이트 · 롤백 · 스케일", exams=["CKA", "CKAD"], cat="배포·릴리스",
     tags=["deployment", "rollout", "rollback", "undo", "set image", "strategy", "maxSurge", "롤백", "배포", "scale"],
     body="""```
k set image deploy/web nginx=nginx:1.27
k rollout status deploy/web
k rollout history deploy/web
k rollout undo deploy/web [--to-revision=2]
k rollout pause|resume|restart deploy/web
k scale deploy web --replicas=5
```
```
spec:
  strategy:
    type: RollingUpdate            # 또는 Recreate
    rollingUpdate: {maxSurge: 25%, maxUnavailable: 25%}
  revisionHistoryLimit: 10
```
- 이미지 변경 이력에 사유를 남기려면 `kubernetes.io/change-cause` annotation 사용
- 롤아웃이 멈추면 `describe deploy`, ReplicaSet/Pod 이벤트(이미지 오류, 프로브 실패) 확인"""),

dict(id="deploy-strategy", title="Blue/Green · Canary 배포 (CKAD)", exams=["CKAD"], cat="배포·릴리스",
     tags=["canary", "blue-green", "bluegreen", "카나리", "블루그린", "릴리스", "selector"],
     body="""**Canary**: 같은 Service selector(`app=web`)에 버전 레이블만 다른 두 Deployment 를 두고 replica 비율로 트래픽 분배
```
web-v1: replicas 9  labels {app: web, ver: v1}
web-v2: replicas 1  labels {app: web, ver: v2}   # ≈10% 트래픽
Service selector: {app: web}
```
**Blue/Green**: 두 Deployment 를 동시 운영하고 Service selector 의 `ver` 값을 전환
```
k patch svc web -p '{"spec":{"selector":{"app":"web","ver":"v2"}}}'
```
- 롤백은 selector 를 되돌리거나 `rollout undo`"""),

dict(id="sched", title="스케줄링: nodeSelector · affinity · taint/toleration", exams=["CKA", "CKAD"], cat="워크로드·스케줄링",
     tags=["taint", "toleration", "affinity", "nodeselector", "nodename", "스케줄링", "anti-affinity", "topology", "pending"],
     body="""```
k taint nodes node01 key=value:NoSchedule        # 추가
k taint nodes node01 key=value:NoSchedule-       # 제거 (끝의 - )
k label node node01 disk=ssd
```
```
spec:
  nodeSelector: {disk: ssd}
  tolerations:
  - {key: key, operator: Equal, value: value, effect: NoSchedule}
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions: [{key: disk, operator: In, values: [ssd]}]
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector: {matchLabels: {app: web}}
        topologyKey: kubernetes.io/hostname
```
- `nodeName` 지정 시 스케줄러를 우회한다
- 컨트롤 플레인 노드 기본 taint: `node-role.kubernetes.io/control-plane:NoSchedule`
- 효과: NoSchedule(신규 차단) / PreferNoSchedule / NoExecute(기존 파드도 축출)"""),

dict(id="resources", title="리소스 requests/limits · Quota · LimitRange · QoS", exams=["CKA", "CKAD"], cat="워크로드·스케줄링",
     tags=["resources", "requests", "limits", "quota", "limitrange", "qos", "oom", "cpu", "memory", "리소스"],
     body="""```
resources:
  requests: {cpu: 100m, memory: 128Mi}
  limits:   {cpu: 500m, memory: 256Mi}
```
```
apiVersion: v1
kind: ResourceQuota
metadata: {name: q, namespace: dev}
spec:
  hard: {pods: "10", requests.cpu: "2", requests.memory: 4Gi, limits.cpu: "4"}
---
apiVersion: v1
kind: LimitRange
metadata: {name: lr, namespace: dev}
spec:
  limits:
  - type: Container
    default: {cpu: 500m, memory: 256Mi}
    defaultRequest: {cpu: 100m, memory: 128Mi}
```
- QoS: Guaranteed(requests=limits) > Burstable > BestEffort. 메모리 부족 시 BestEffort 부터 축출
- 메모리 limit 초과 → **OOMKilled**, CPU limit 초과 → 스로틀링
- Quota 로 requests/limits 를 강제하면 미지정 파드는 생성 거부 → LimitRange 로 기본값 제공
- 사용량: `k top pod|node` (metrics-server 필요)"""),

dict(id="hpa", title="HPA (Horizontal Pod Autoscaler)", exams=["CKA", "CKAD"], cat="워크로드·스케줄링",
     tags=["hpa", "autoscale", "autoscaler", "metrics-server", "오토스케일", "scale"],
     body="""```
k autoscale deploy web --min=2 --max=10 --cpu-percent=50   # 버전에 따라 --cpu=50% 형식
k get hpa -w
```
- 대상 컨테이너에 **cpu requests 가 있어야** 퍼센트 계산 가능, metrics-server 필수
- `TARGETS <unknown>/50%` → metrics-server 미설치 또는 requests 미설정
- 축소 안정화 기본 5분 (`behavior.scaleDown.stabilizationWindowSeconds`)"""),

dict(id="static-ds", title="DaemonSet · Static Pod", exams=["CKA"], cat="워크로드·스케줄링",
     tags=["daemonset", "static pod", "staticpod", "manifests", "kubelet", "스태틱"],
     body="""# Static Pod
- kubelet 이 `/etc/kubernetes/manifests` (설정 `staticPodPath` in `/var/lib/kubelet/config.yaml`)의 YAML 을 직접 실행
- 파드 이름에 노드명이 붙는다 (예: `web-node01`). API 서버에서 삭제해도 재생성 → **파일을 지워야** 삭제됨
```
k run static-web --image=nginx $do > /etc/kubernetes/manifests/static-web.yaml
```
- 컨트롤 플레인 컴포넌트(apiserver, etcd, scheduler, controller-manager)도 static pod
# DaemonSet
- 노드마다 1개 파드 (로그/모니터링 에이전트). `kind: DaemonSet`, `replicas` 없음
- 컨트롤 플레인에도 올리려면 toleration 필요"""),

dict(id="pod-multi", title="멀티 컨테이너 · initContainer · Sidecar", exams=["CKAD"], cat="워크로드·스케줄링",
     tags=["sidecar", "initcontainer", "init", "multi-container", "emptydir", "adapter", "ambassador", "사이드카"],
     body="""```
spec:
  initContainers:
  - name: wait-db
    image: busybox
    command: ['sh','-c','until nslookup db; do sleep 2; done']
  containers:
  - {name: app, image: nginx, volumeMounts: [{name: logs, mountPath: /var/log/nginx}]}
  - {name: shipper, image: busybox, command: ['sh','-c','tail -F /logs/access.log'], volumeMounts: [{name: logs, mountPath: /logs}]}
  volumes:
  - {name: logs, emptyDir: {}}
```
- initContainer 는 순차 실행, 모두 성공해야 앱 컨테이너 시작
- 네이티브 사이드카(v1.29+): `initContainers` 항목에 `restartPolicy: Always`
- 컨테이너 선택: `k logs pod -c shipper`, `k exec -it pod -c app -- sh`"""),

dict(id="job-cron", title="Job · CronJob", exams=["CKAD"], cat="워크로드·스케줄링",
     tags=["job", "cronjob", "completions", "parallelism", "backoffLimit", "schedule", "배치"],
     body="""```
k create job pi --image=perl -- perl -Mbignum=bpi -wle 'print bpi(2000)'
k create cronjob hello --image=busybox --schedule="*/1 * * * *" -- date
k create job manual-run --from=cronjob/hello
```
```
spec:                       # Job
  completions: 5
  parallelism: 2
  backoffLimit: 4
  activeDeadlineSeconds: 120
  ttlSecondsAfterFinished: 60
  template: {spec: {restartPolicy: Never, containers: [...]}}   # Never 또는 OnFailure
# CronJob 추가 필드
  concurrencyPolicy: Forbid   # Allow | Forbid | Replace
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```"""),

# ------------------------------------------------------------------ 구성·보안
dict(id="cm-secret", title="ConfigMap · Secret 주입", exams=["CKAD", "CKA"], cat="구성·보안",
     tags=["configmap", "secret", "env", "envfrom", "volume", "구성", "환경변수", "시크릿"],
     body="""```
k create cm app --from-literal=MODE=prod --from-file=app.properties
k create secret generic db --from-literal=password=s3cr3t
k create secret docker-registry reg --docker-server=... --docker-username=... --docker-password=...
```
```
containers:
- name: app
  envFrom: [{configMapRef: {name: app}}]
  env:
  - name: DB_PASS
    valueFrom: {secretKeyRef: {name: db, key: password}}
  volumeMounts: [{name: cfg, mountPath: /etc/app}]
volumes:
- name: cfg
  configMap: {name: app}        # 키가 파일로 마운트됨
```
- env 로 주입한 값은 **파드 재시작 전에는 갱신되지 않음**, 볼륨 마운트는 자동 갱신(subPath 제외)
- Secret 은 base64 **인코딩**일 뿐 암호화가 아님 → `echo -n val | base64`, 확인 `base64 -d`
- `CreateContainerConfigError` → 참조한 ConfigMap/Secret/key 오타 확인"""),

dict(id="secctx-sa", title="SecurityContext · ServiceAccount", exams=["CKAD", "CKA"], cat="구성·보안",
     tags=["securitycontext", "runasuser", "serviceaccount", "capabilities", "privileged", "fsgroup", "보안"],
     body="""```
spec:
  serviceAccountName: build-sa
  automountServiceAccountToken: false
  securityContext: {runAsUser: 1000, runAsGroup: 3000, fsGroup: 2000}   # 파드 수준
  containers:
  - name: app
    image: nginx
    securityContext:                                                    # 컨테이너 수준(우선)
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      capabilities: {drop: ["ALL"], add: ["NET_BIND_SERVICE"]}
```
```
k create sa build-sa
k create token build-sa          # 단기 토큰 발급 (v1.24+)
k set serviceaccount deploy/web build-sa
```
- 컨테이너 수준 설정이 파드 수준 설정을 덮어쓴다"""),

# ------------------------------------------------------------------ 서비스·네트워킹
dict(id="service", title="Service 타입과 Endpoint 점검", exams=["CKA", "CKAD"], cat="서비스·네트워킹",
     tags=["service", "clusterip", "nodeport", "loadbalancer", "headless", "externalname", "endpoints", "selector", "서비스"],
     body="""```
k expose deploy web --port=80 --target-port=8080 --type=ClusterIP
k get svc,endpoints,endpointslices -o wide
```
- ClusterIP(내부) / NodePort(30000-32767) / LoadBalancer / ExternalName(CNAME) / Headless(`clusterIP: None`, DNS 가 파드 IP 반환)
- **Endpoints 가 비어 있으면** selector↔파드 label 불일치 또는 readiness 실패
- `port`(서비스 포트) vs `targetPort`(컨테이너 포트) 혼동 주의
- 내부 접근 테스트: `k run t --rm -it --image=busybox:1.36 --restart=Never -- wget -qO- svc.ns:80`"""),

dict(id="ingress", title="Ingress · Gateway API", exams=["CKA", "CKAD"], cat="서비스·네트워킹",
     tags=["ingress", "gateway", "httproute", "ingressclass", "tls", "path", "인그레스"],
     body="""```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata: {name: web}
spec:
  ingressClassName: nginx
  rules:
  - host: foo.com
    http:
      paths:
      - {path: /app, pathType: Prefix, backend: {service: {name: web, port: {number: 80}}}}
```
```
k create ingress web --class=nginx --rule="foo.com/app*=web:80" $do
k get ingressclass ; k describe ingress web
```
- `ingressClassName` 누락 시 동작 안 함, Ingress Controller 가 설치돼 있어야 함
- **Gateway API**: `GatewayClass` → `Gateway`(listener) → `HTTPRoute`(parentRefs, rules[].backendRefs) 구조
- 확인: `k get gateway,httproute`"""),

dict(id="netpol", title="NetworkPolicy", exams=["CKA", "CKAD"], cat="서비스·네트워킹",
     tags=["networkpolicy", "network policy", "ingress", "egress", "podselector", "namespaceselector", "네트워크정책", "방화벽"],
     body="""```
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: db-allow, namespace: prod}
spec:
  podSelector: {matchLabels: {app: db}}
  policyTypes: [Ingress, Egress]
  ingress:
  - from:
    - podSelector: {matchLabels: {app: api}}
    - namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: staging}}
    ports: [{protocol: TCP, port: 5432}]
  egress:
  - to: [{namespaceSelector: {}}]
    ports: [{protocol: UDP, port: 53}]       # DNS 허용 필수
```
- `from` 안에서 **같은 항목(-) 내 selector 는 AND**, **항목이 나뉘면 OR** (가장 흔한 함정)
- policyTypes 에 명시한 방향은 허용 규칙이 없으면 **전부 차단**. 빈 `podSelector: {}` = 네임스페이스 전체 파드
- egress 제한 시 DNS(UDP/TCP 53) 허용을 잊지 말 것
- CNI 가 NetworkPolicy 를 지원해야 함 (Calico, Cilium 등)"""),

dict(id="dns", title="클러스터 DNS / CoreDNS", exams=["CKA", "CKAD"], cat="서비스·네트워킹",
     tags=["dns", "coredns", "nslookup", "resolv", "svc.cluster.local", "kube-dns", "이름해석"],
     body="""```
k -n kube-system get pods -l k8s-app=kube-dns
k -n kube-system logs -l k8s-app=kube-dns
k -n kube-system get cm coredns -o yaml
k run t --rm -it --image=busybox:1.36 --restart=Never -- nslookup kubernetes.default
```
- 서비스: `<svc>.<ns>.svc.cluster.local`, 파드: `<ip-with-dashes>.<ns>.pod.cluster.local`
- 파드의 `/etc/resolv.conf` 에 nameserver(kube-dns ClusterIP)와 search 도메인 확인
- CoreDNS 가 CrashLoop → Corefile 의 `loop`, upstream resolver(`/etc/resolv.conf` of node) 문제 확인"""),

# ------------------------------------------------------------------ 스토리지
dict(id="pv-pvc", title="PV · PVC · StorageClass", exams=["CKA", "CKAD"], cat="스토리지",
     tags=["pv", "pvc", "storageclass", "persistentvolume", "accessmodes", "reclaim", "hostpath", "볼륨", "스토리지"],
     body="""```
apiVersion: v1
kind: PersistentVolume
metadata: {name: pv1}
spec:
  capacity: {storage: 1Gi}
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath: {path: /mnt/data}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata: {name: pvc1}
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: manual
  resources: {requests: {storage: 500Mi}}
```
```
# 파드에서 사용
volumes: [{name: data, persistentVolumeClaim: {claimName: pvc1}}]
```
- PVC 가 **Pending**: storageClassName/accessModes/용량 불일치, 가용 PV 없음, `volumeBindingMode: WaitForFirstConsumer` (파드 생성 후 바인딩)
- accessModes: RWO / ROX / RWX / RWOP. reclaimPolicy: Retain / Delete
- 확장: StorageClass 에 `allowVolumeExpansion: true` 이면 PVC `requests.storage` 증가
- 기본 SC 지정: annotation `storageclass.kubernetes.io/is-default-class: "true"`"""),

# ------------------------------------------------------------------ 관찰·디버깅
dict(id="probes", title="Liveness · Readiness · Startup 프로브", exams=["CKAD", "CKA"], cat="관찰·디버깅",
     tags=["probe", "liveness", "readiness", "startup", "healthcheck", "프로브", "헬스체크"],
     body="""```
livenessProbe:
  httpGet: {path: /healthz, port: 8080}
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3
readinessProbe:
  exec: {command: [cat, /tmp/ready]}
startupProbe:
  tcpSocket: {port: 8080}
  failureThreshold: 30
  periodSeconds: 10
```
- **liveness 실패 → 컨테이너 재시작**, **readiness 실패 → Service 엔드포인트에서 제외**(재시작 안 함), startup 은 성공 전까지 다른 프로브 보류
- 프로브 실패 확인: `k describe pod` Events (`Liveness probe failed: ...`)
- 느린 앱에 liveness 를 너무 빡빡하게 두면 CrashLoop → startupProbe 사용"""),

dict(id="logs-debug", title="로그 · exec · port-forward · debug · top", exams=["CKA", "CKAD"], cat="관찰·디버깅",
     tags=["logs", "exec", "port-forward", "debug", "top", "events", "describe", "로그", "디버깅", "metrics"],
     body="""```
k logs pod -f --tail=50 [-c container] [--previous] [-l app=web --all-containers]
k exec -it pod -- sh
k port-forward svc/web 8080:80
k describe pod pod | sed -n '/Events/,$p'
k get events -A --sort-by=.metadata.creationTimestamp
k top pod -A --sort-by=memory ; k top node
k debug -it pod --image=busybox:1.36 --target=app      # 임시 디버그 컨테이너
k debug node/node01 -it --image=busybox                # 노드 디버그 (호스트 /host)
k cp pod:/path/file ./file
```
- `--previous` : 직전에 죽은 컨테이너 로그 (CrashLoopBackOff 필수 명령)
- API deprecation 점검: `k api-versions`, `k explain`, `k convert` (플러그인)"""),

# ------------------------------------------------------------------ 트러블슈팅
dict(id="ts-pod", title="Pod 상태별 트러블슈팅 표", exams=["CKA", "CKAD"], cat="트러블슈팅",
     tags=["pending", "crashloopbackoff", "imagepullbackoff", "oomkilled", "evicted", "createcontainerconfigerror", "error", "파드", "장애"],
     body="""| 상태 | 주요 원인 | 확인/조치 |
|---|---|---|
| Pending | 스케줄 불가(리소스·taint·affinity), PVC 미바인딩 | `describe pod` Events, `describe node`, `get pvc` |
| ImagePullBackOff / ErrImagePull | 이미지명/태그 오타, 레지스트리 인증 | `describe pod`, imagePullSecrets, `crictl pull` |
| CrashLoopBackOff | 앱 에러, 잘못된 command/args, 프로브 실패, OOM | `logs --previous`, `describe` Last State/Exit Code |
| CreateContainerConfigError | ConfigMap/Secret/key 없음 | 참조 이름 확인 |
| OOMKilled (Exit 137) | 메모리 limit 초과 | limit 상향/누수 점검 |
| Evicted | 노드 자원 압박(disk/memory) | `describe node` Conditions |
| Running 이지만 접속 불가 | readiness 실패, Service selector/포트 불일치 | `get endpoints`, `describe svc` |
| Terminating 정체 | finalizer, 노드 다운 | `k delete pod x --force --grace-period=0` |
```
k get pod -o wide ; k describe pod x ; k logs x --previous ; k get events --sort-by=.metadata.creationTimestamp
```"""),

dict(id="ts-node", title="노드 NotReady 트러블슈팅", exams=["CKA"], cat="트러블슈팅",
     tags=["notready", "node", "kubelet", "containerd", "노드", "swap", "cni", "certificate"],
     body="""```
k get nodes ; k describe node node01      # Conditions: Ready, MemoryPressure, DiskPressure, PIDPressure
ssh node01
systemctl status kubelet ; journalctl -u kubelet -f --no-pager | tail -50
systemctl status containerd ; crictl ps -a
```
체크리스트
1. kubelet 미기동 → `systemctl enable --now kubelet`
2. kubelet 설정 오류: `/var/lib/kubelet/config.yaml`, `/etc/kubernetes/kubelet.conf`(apiserver 주소/인증서 경로), drop-in `/etc/systemd/system/kubelet.service.d/10-kubeadm.conf`
3. 설정 변경 후 `systemctl daemon-reload && systemctl restart kubelet`
4. containerd 중지/소켓 경로 불일치, swap 활성화, CNI 미설치(`/etc/cni/net.d`, `/opt/cni/bin`)
5. 인증서 만료: `kubeadm certs check-expiration`, `kubeadm certs renew all`
6. 디스크/메모리 압박 → `df -h`, `free -m`"""),

dict(id="ts-controlplane", title="컨트롤 플레인 장애 (apiserver · scheduler · etcd)", exams=["CKA"], cat="트러블슈팅",
     tags=["apiserver", "scheduler", "controller-manager", "etcd", "manifests", "컨트롤플레인", "control plane", "static pod"],
     body="""컨트롤 플레인은 static pod → 매니페스트: `/etc/kubernetes/manifests/*.yaml`
```
crictl ps -a | grep -E 'apiserver|etcd|scheduler|controller'
crictl logs <container-id>
ls /var/log/pods ; journalctl -u kubelet | tail
k -n kube-system get pods
```
| 증상 | 의심 컴포넌트 |
|---|---|
| `kubectl` 이 연결 거부 | kube-apiserver 다운 → 매니페스트 오타, 인증서 경로, etcd 주소(`--etcd-servers`) |
| 새 파드가 계속 Pending (Events 없음) | kube-scheduler 다운/설정 오류 |
| Deployment 가 ReplicaSet/파드를 만들지 않음 | kube-controller-manager 다운 |
| apiserver 가 계속 재시작 | etcd 다운/인증서 불일치 |
- 매니페스트 수정 후 kubelet 이 자동 재생성 (수십 초). 안 되면 파일을 잠시 다른 곳으로 옮겼다 되돌림
- 흔한 오타: 인증서 경로, 포트, `--` 플래그 철자, hostPath 경로, 이미지 태그"""),

dict(id="ts-svc-net", title="서비스/네트워크 연결 문제 점검 순서", exams=["CKA", "CKAD"], cat="트러블슈팅",
     tags=["service", "endpoint", "network", "연결", "접속불가", "kube-proxy", "cni", "connection refused", "timeout"],
     body="""위에서 아래로 좁혀 간다.
1. 파드 Running/Ready 인가? `k get pod -o wide`
2. 파드 직접 접속: `k exec t -- wget -qO- <podIP>:<targetPort>`
3. Service endpoints 존재? `k get endpoints svc` → 비어있으면 selector/label, readiness 확인
4. Service 접속: `<svc>.<ns>:<port>` (DNS 확인 → CoreDNS 노트)
5. `targetPort` 가 컨테이너 포트와 일치?
6. NetworkPolicy 가 막는가? `k get netpol -A`
7. kube-proxy 상태: `k -n kube-system get pods -l k8s-app=kube-proxy`, 로그
8. CNI 파드(calico/cilium/flannel) 상태와 `/etc/cni/net.d`
9. Ingress: `ingressClassName`, backend 서비스·포트, controller 로그"""),

dict(id="ts-app-logs", title="애플리케이션 장애 분석 (CKAD)", exams=["CKAD"], cat="트러블슈팅",
     tags=["application", "failure", "debug", "앱", "로그", "deprecated", "애플리케이션"],
     body="""1. `k get pods` 상태 확인 → 표(Pod 상태별 트러블슈팅) 로 원인 분류
2. `k logs <pod> [-c c] [--previous]`, `k describe pod`
3. 구성 문제: env/ConfigMap/Secret 참조, 볼륨 마운트 경로, command/args 오타
4. 네트워크 문제: Service selector/port, NetworkPolicy, Ingress
5. 리소스 문제: limits(OOMKilled), Quota 초과 (`k describe quota -n ns`)
6. 수정은 `k edit` 또는 YAML 수정 후 `k replace --force -f pod.yaml` (파드의 불변 필드 변경 시)
- `k get deploy,rs,pod -l app=web` 으로 계층을 한눈에 확인"""),
]
