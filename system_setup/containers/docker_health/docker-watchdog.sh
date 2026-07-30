#!/usr/bin/env bash

# ============================================
# 通用 Docker 容器守护进程
#
# 两级策略:
#   monitor  - 只收集日志/状态/告警, 不重启
#   autoheal - 收集 + 受控重启 (连续失败阈值 + cooldown + 速率限制)
#
# 策略来源优先级: EXCLUDE > label(watchdog.policy) > ENV 名单 > 默认忽略
# 自身容器自动加入 EXCLUDE (运行在容器内时)
#
# 主要函数:
#   resolve_policy          解析单个容器的策略
#   match_name_list         按 glob 匹配 name 是否在逗号分隔的列表中
#   state_get / state_set   读写持久化状态
#   should_restart          重启决策 (cooldown + 速率)
#   collect_container_*     取证 (日志 / stats / inspect / healthcheck)
#   process_container       单容器处理主流程
# ============================================

set -uo pipefail

# ---------- 配置 ----------
CHECK_INTERVAL=${CHECK_INTERVAL:-30}              # 检查间隔(秒)
LOG_LINES=${LOG_LINES:-1000}                      # 收集日志行数
LOG_DIR=${LOG_DIR:-"./container_logs"}            # 日志目录
STATE_DIR=${STATE_DIR:-"$LOG_DIR/.state"}         # 状态持久化目录
LOG_RETENTION_DAYS=${LOG_RETENTION_DAYS:-7}       # 日志保留天数

UNHEALTHY_THRESHOLD=${UNHEALTHY_THRESHOLD:-3}     # 连续 unhealthy 多少次才触发动作
RESTART_COOLDOWN=${RESTART_COOLDOWN:-600}         # 同容器两次重启最短间隔(秒)
RESTART_MAX_PER_HOUR=${RESTART_MAX_PER_HOUR:-3}   # 单容器每小时最大重启次数
START_GRACE_PERIOD=${START_GRACE_PERIOD:-120}     # 容器启动后宽限期(秒), 期间忽略 unhealthy
DUMP_COOLDOWN=${DUMP_COOLDOWN:-1800}              # 两次取证最短间隔(秒), 避免持续故障刷盘

# 名单 (逗号分隔, 支持 shell glob 如 "vllm-*,whisper-asr")
WATCHDOG_AUTOHEAL_NAMES=${WATCHDOG_AUTOHEAL_NAMES:-""}
WATCHDOG_MONITOR_NAMES=${WATCHDOG_MONITOR_NAMES:-""}
WATCHDOG_EXCLUDE_NAMES=${WATCHDOG_EXCLUDE_NAMES:-""}

LABEL_KEY=${LABEL_KEY:-"watchdog.policy"}         # 容器 label 键名

# 可选: 外部告警钩子(接收 msg 作为 argv1), 例如调用 curl 推送到 webhook
WATCHDOG_NOTIFY_HOOK=${WATCHDOG_NOTIFY_HOOK:-""}

mkdir -p "$LOG_DIR" "$STATE_DIR"

# ---------- 日志与告警 ----------
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [docker-watchdog] $*"
}

# 关键事件: 本地日志 + syslog + 外部 hook
notify() {
    local msg="$*"
    log "$msg"
    command -v logger >/dev/null 2>&1 && logger -t docker-watchdog "$msg"
    if [ -n "$WATCHDOG_NOTIFY_HOOK" ]; then
        "$WATCHDOG_NOTIFY_HOOK" "$msg" >/dev/null 2>&1 || true
    fi
}

# ---------- 自身检测 ----------
# 容器内运行时返回自己的 container id; 宿主机运行返回空
get_self_container_id() {
    if [ -r /proc/self/cgroup ]; then
        local id
        id=$(grep -oE '[0-9a-f]{64}' /proc/self/cgroup 2>/dev/null | head -n1)
        if [ -n "$id" ]; then
            echo "$id"; return
        fi
    fi
    # 退化: 容器内 HOSTNAME 通常就是 short id (12 位 hex)
    if [ -n "${HOSTNAME:-}" ] && [ "${#HOSTNAME}" -ge 12 ] \
       && [ -z "${HOSTNAME//[0-9a-f]/}" ]; then
        echo "$HOSTNAME"; return
    fi
    echo ""
}

# ---------- 名单匹配 ----------
# match_name_list <name> <comma-separated-glob-list> -> 0 命中 / 1 未命中
match_name_list() {
    local name="$1" list="$2"
    [ -z "$list" ] && return 1
    local IFS=','
    local pattern
    for pattern in $list; do
        # 去首尾空白
        pattern="${pattern#"${pattern%%[![:space:]]*}"}"
        pattern="${pattern%"${pattern##*[![:space:]]}"}"
        [ -z "$pattern" ] && continue
        # shellcheck disable=SC2254
        case "$name" in
            $pattern) return 0 ;;
        esac
    done
    return 1
}

# ---------- 策略解析 ----------
# 输出: autoheal | monitor | ignore
resolve_policy() {
    local container_id="$1" container_name="$2"

    # 1. 自身排除 (短 id 和长 id 互相是前缀)
    if [ -n "$SELF_CID" ]; then
        if [ "${container_id#"$SELF_CID"}" != "$container_id" ] \
           || [ "${SELF_CID#"$container_id"}" != "$SELF_CID" ]; then
            echo "ignore"; return
        fi
    fi

    # 2. EXCLUDE 名单 (最高优先级)
    if match_name_list "$container_name" "$WATCHDOG_EXCLUDE_NAMES"; then
        echo "ignore"; return
    fi

    # 3. label 优先于 ENV 名单 (with 守护避免 Labels 为 nil 时模板报错)
    local label_val
    label_val=$(docker inspect --format "{{ with .Config.Labels }}{{ index . \"$LABEL_KEY\" }}{{ end }}" "$container_id" 2>/dev/null)
    case "$label_val" in
        autoheal|monitor) echo "$label_val"; return ;;
    esac

    # 4. ENV 名单兜底
    if match_name_list "$container_name" "$WATCHDOG_AUTOHEAL_NAMES"; then
        echo "autoheal"; return
    fi
    if match_name_list "$container_name" "$WATCHDOG_MONITOR_NAMES"; then
        echo "monitor"; return
    fi

    # 5. 默认忽略 (安全默认值)
    echo "ignore"
}

# 文件名净化: 替换非 [A-Za-z0-9_.-] 的字符为下划线 (Docker 名规则更窄, 但留个防御层)
# 用 printf 而非 echo 避免 tr 把尾部换行转成下划线
safe_key() {
    printf '%s' "$1" | tr -c 'A-Za-z0-9_.-' '_'
}

# ---------- 状态持久化 (单文件 key=value) ----------
state_file() {
    local key; key=$(safe_key "$1")
    echo "$STATE_DIR/${key}.state"
}

state_get() {
    local name="$1" key="$2" default="${3:-}"
    local f; f=$(state_file "$name")
    [ -f "$f" ] || { echo "$default"; return; }
    local v
    v=$(grep "^${key}=" "$f" 2>/dev/null | tail -n1 | cut -d= -f2-)
    [ -z "$v" ] && v="$default"
    echo "$v"
}

state_set() {
    local name="$1" key="$2" val="$3"
    local f; f=$(state_file "$name")
    touch "$f"
    if grep -q "^${key}=" "$f" 2>/dev/null; then
        local tmp="${f}.tmp.$$"
        grep -v "^${key}=" "$f" > "$tmp"
        echo "${key}=${val}" >> "$tmp"
        mv "$tmp" "$f"
    else
        echo "${key}=${val}" >> "$f"
    fi
}

# ---------- 重启决策 ----------
# 允许重启返回 0; 拒绝时返回 1 并将原因输出到 stdout
should_restart() {
    local name="$1"
    local now; now=$(date +%s)

    # cooldown 检查
    local last; last=$(state_get "$name" "last_restart" "0")
    # 防止脏 state 文件导致算术报错
    case "$last" in
        ''|*[!0-9]*) last=0 ;;
    esac
    if [ "$((now - last))" -lt "$RESTART_COOLDOWN" ]; then
        echo "cooldown 中 (还剩 $((RESTART_COOLDOWN - (now - last))) 秒)"
        return 1
    fi

    # 裁剪并统计过去 1 小时内的重启次数
    local history; history=$(state_get "$name" "restart_history" "")
    local count=0 kept=""
    if [ -n "$history" ]; then
        local IFS=','
        local ts
        for ts in $history; do
            [ -z "$ts" ] && continue
            # 跳过脏数据
            case "$ts" in *[!0-9]*) continue ;; esac
            if [ "$((now - ts))" -lt 3600 ]; then
                count=$((count + 1))
                kept="${kept:+$kept,}$ts"
            fi
        done
    fi
    # 总是写回裁剪后的 history, 避免无限增长
    state_set "$name" "restart_history" "$kept"

    if [ "$count" -ge "$RESTART_MAX_PER_HOUR" ]; then
        echo "已达每小时最大重启次数 ($count/$RESTART_MAX_PER_HOUR)"
        return 1
    fi
    return 0
}

record_restart() {
    local name="$1"
    local now; now=$(date +%s)
    state_set "$name" "last_restart" "$now"
    local history; history=$(state_get "$name" "restart_history" "")
    history="${history:+$history,}$now"
    state_set "$name" "restart_history" "$history"
}

# ---------- 取证 ----------
collect_container_stats() {
    local container_id="$1" stats_file="$2"

    {
        echo "=============== 容器基本信息 ==============="
        docker inspect --format='创建时间:      {{.Created}}
启动时间:      {{.State.StartedAt}}
结束时间:      {{.State.FinishedAt}}
当前状态:      {{.State.Status}}
健康状态:      {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}
FailingStreak: {{if .State.Health}}{{.State.Health.FailingStreak}}{{else}}0{{end}}
重启次数:      {{.RestartCount}}
退出码:        {{.State.ExitCode}}
OOMKilled:     {{.State.OOMKilled}}
错误信息:      {{.State.Error}}' "$container_id" 2>/dev/null \
            || echo "警告: 无法获取容器基本信息"
        echo ""

        echo "=============== Healthcheck 详情 ==============="
        # State.Health.Log 包含最近几次 healthcheck 的 stdout/exit_code/时间, 是排障金矿
        docker inspect --format='{{json .State.Health}}' "$container_id" 2>/dev/null \
            || echo "无 Healthcheck 信息"
        echo ""

        echo "=============== 资源使用情况 ==============="
        docker stats --no-stream \
            --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" \
            "$container_id" 2>/dev/null \
            || echo "警告: 无法获取资源使用"
        echo ""

        echo "=============== 容器进程 ==============="
        docker top "$container_id" 2>/dev/null \
            || echo "警告: 无法获取进程信息 (容器可能未运行)"
        echo ""
    } >> "$stats_file"
}

collect_container_logs() {
    local container_id="$1" container_name="$2" policy="$3"
    local timestamp safe_name short_id
    timestamp=$(date '+%Y%m%d_%H%M%S')
    # 文件名: safe(name) + timestamp + short_id, 既能按 name glob 分组, 又能区分重建后的不同实例
    safe_name=$(safe_key "$container_name")
    short_id="${container_id:0:12}"
    local log_file="$LOG_DIR/${safe_name}_${timestamp}_${short_id}.log"

    log "收集 $container_name 的状态和最近 $LOG_LINES 行日志 -> $log_file"

    {
        echo "=========================================="
        echo "容器名称: $container_name"
        echo "容器ID:   $container_id"
        echo "策略:     $policy"
        echo "收集时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "日志行数: $LOG_LINES"
        echo "=========================================="
        echo ""
    } > "$log_file"

    collect_container_stats "$container_id" "$log_file"

    echo "================= 容器日志 =================" >> "$log_file"
    docker logs --tail "$LOG_LINES" "$container_id" >> "$log_file" 2>&1 \
        || echo "错误: 无法获取容器日志" >> "$log_file"
}

# 受 DUMP_COOLDOWN 限制的取证; 在 cooldown 内返回 1 且不写文件
maybe_dump_logs() {
    local container_id="$1" container_name="$2" policy="$3"
    local last_dump; last_dump=$(state_get "$container_name" "last_dump" "0")
    local now_ts; now_ts=$(date +%s)
    if [ "$((now_ts - last_dump))" -lt "$DUMP_COOLDOWN" ]; then
        return 1
    fi
    collect_container_logs "$container_id" "$container_name" "$policy"
    state_set "$container_name" "last_dump" "$now_ts"
    return 0
}

# 取 max(全局 START_GRACE_PERIOD, 容器自身 healthcheck.StartPeriod)
# 关键: 必须用 printf "%d" 强制按整数输出, 默认模板会走 Duration.String() 返回 "5s" 字符串
get_effective_grace_period() {
    local container_id="$1"
    local start_period_ns
    start_period_ns=$(docker inspect --format '{{if .Config.Healthcheck}}{{printf "%d" .Config.Healthcheck.StartPeriod}}{{else}}0{{end}}' "$container_id" 2>/dev/null || echo 0)
    case "$start_period_ns" in
        ''|*[!0-9]*) start_period_ns=0 ;;
    esac
    local start_period_sec=$((start_period_ns / 1000000000))
    if [ "$start_period_sec" -gt "$START_GRACE_PERIOD" ]; then
        echo "$start_period_sec"
    else
        echo "$START_GRACE_PERIOD"
    fi
}

# ---------- 单容器处理 ----------
process_container() {
    local container_id="$1"

    # 拉取容器信息 (合并到一次 inspect 减少调用)
    local info container_name started_at status
    info=$(docker inspect --format='{{.Name}}|{{.State.StartedAt}}|{{.State.Status}}' \
           "$container_id" 2>/dev/null)
    if [ -z "$info" ]; then
        log "跳过 $container_id (无法 inspect)"
        return
    fi
    container_name=$(echo "$info" | cut -d'|' -f1 | sed 's|^/||')
    started_at=$(echo "$info" | cut -d'|' -f2)
    status=$(echo "$info" | cut -d'|' -f3)
    [ -z "$container_name" ] && container_name="${container_id:0:12}"

    # 跳过正在重启的容器, 避免叠加干扰
    if [ "$status" = "restarting" ]; then
        log "跳过 $container_name (状态: restarting)"
        return
    fi

    # 启动宽限期: 容器刚起还在初始化时不要插手
    # 取 max(全局 START_GRACE_PERIOD, 容器自身 healthcheck.StartPeriod), 对 vLLM 这种长加载尤其重要
    if [ -n "$started_at" ]; then
        local start_ts now_ts uptime grace_period
        start_ts=$(date -d "$started_at" +%s 2>/dev/null || echo 0)
        now_ts=$(date +%s)
        uptime=$((now_ts - start_ts))
        grace_period=$(get_effective_grace_period "$container_id")
        if [ "$start_ts" -gt 0 ] && [ "$uptime" -lt "$grace_period" ]; then
            log "跳过 $container_name (启动 ${uptime}s, 在宽限期 ${grace_period}s 内)"
            return
        fi
    fi

    # 解析策略
    local policy
    policy=$(resolve_policy "$container_id" "$container_name")
    [ "$policy" = "ignore" ] && return

    # 连续失败计数 +1
    local consec
    consec=$(state_get "$container_name" "consecutive_unhealthy" "0")
    consec=$((consec + 1))
    state_set "$container_name" "consecutive_unhealthy" "$consec"

    # 边沿触发模型:
    #   consec == 1         → notify "首次检测", 关键事件
    #   1 < consec < thresh → 仅本地 log, 不进 syslog
    #   consec == thresh    → notify "达到阈值", 触发动作
    #   consec > thresh     → 静默评估动作 (受 cooldown 节流), 不再 notify 阈值类消息
    # consec 不在动作后清零, 仅由 reset_healthy_container_counters 在容器恢复时清零
    # 这样 "持续故障" 和 "新故障" 在状态文件里一眼可分
    if [ "$consec" -eq 1 ]; then
        notify "容器 $container_name 检测到不健康 (策略: $policy)"
    fi
    if [ "$consec" -lt "$UNHEALTHY_THRESHOLD" ]; then
        [ "$consec" -gt 1 ] && log "容器 $container_name 持续不健康 ($consec/$UNHEALTHY_THRESHOLD)"
        return
    fi

    # 跨越阈值的那一刻
    local crossing="false"
    if [ "$consec" -eq "$UNHEALTHY_THRESHOLD" ]; then
        crossing="true"
        notify "容器 $container_name 累计 $consec 次不健康, 触发 $policy 策略"
    fi

    # monitor 级: 受 DUMP_COOLDOWN 限制取证, 不重启
    if [ "$policy" = "monitor" ]; then
        if maybe_dump_logs "$container_id" "$container_name" "$policy"; then
            notify "monitor 取证完成: $container_name"
        elif [ "$crossing" = "true" ]; then
            log "$container_name monitor 取证 cooldown 中, 跳过"
        fi
        return
    fi

    # autoheal 级: 先决策
    local reason
    if ! reason=$(should_restart "$container_name"); then
        # 限流时: 跨越的一刻 notify, 后续每轮仅本地 log, 避免 syslog 刷屏
        if [ "$crossing" = "true" ]; then
            notify "容器 $container_name 自愈限流: $reason (本次仅记录)"
        else
            log "$container_name 自愈限流: $reason"
        fi
        maybe_dump_logs "$container_id" "$container_name" "$policy" || true
        return
    fi

    # 重启前强制取证 (无视 DUMP_COOLDOWN, 这是最关键的现场快照)
    collect_container_logs "$container_id" "$container_name" "$policy"
    state_set "$container_name" "last_dump" "$(date +%s)"

    notify "开始重启容器 $container_name"
    # 不管成败都记录尝试, 让 cooldown / 速率限制应用于尝试本身, Docker 故障时不会无脑重试
    record_restart "$container_name"
    if docker restart "$container_id" >/dev/null 2>&1; then
        notify "容器 $container_name 重启成功"
    else
        notify "错误: 容器 $container_name 重启失败"
    fi
}

# 健康容器需要清除累计计数, 否则历史失败会叠加触发误判
reset_healthy_container_counters() {
    local healthy_names
    healthy_names=$(docker ps --filter "health=healthy" --format "{{.Names}}" 2>/dev/null)
    [ -z "$healthy_names" ] && return
    local name
    while read -r name; do
        [ -z "$name" ] && continue
        local f; f=$(state_file "$name")
        [ -f "$f" ] || continue
        local consec
        consec=$(state_get "$name" "consecutive_unhealthy" "0")
        if [ "$consec" != "0" ]; then
            state_set "$name" "consecutive_unhealthy" "0"
        fi
    done <<< "$healthy_names"
}

rotate_logs() {
    find "$LOG_DIR" -maxdepth 1 -type f -name "*.log" \
        -mtime "+${LOG_RETENTION_DAYS}" -delete 2>/dev/null || true
}

# ---------- 并发保护 ----------
LOCK_FILE="${STATE_DIR}/watchdog.lock"
exec 9>"$LOCK_FILE"
if command -v flock >/dev/null 2>&1; then
    flock -n 9 || { log "另一个 watchdog 实例已在运行, 退出"; exit 0; }
fi

# ---------- 启动 ----------
SELF_CID=$(get_self_container_id)
log "守护进程已启动"
log "配置 - 间隔: ${CHECK_INTERVAL}s, 阈值: ${UNHEALTHY_THRESHOLD} 次, 重启 cooldown: ${RESTART_COOLDOWN}s, 速率: ${RESTART_MAX_PER_HOUR}/h"
log "配置 - 启动宽限期: ${START_GRACE_PERIOD}s, 取证 cooldown: ${DUMP_COOLDOWN}s, 日志保留: ${LOG_RETENTION_DAYS} 天"
log "日志目录: $LOG_DIR, 状态目录: $STATE_DIR"
[ -n "$SELF_CID" ] && log "检测到自身容器 ID: ${SELF_CID:0:12} (已自动排除)"
[ -n "$WATCHDOG_EXCLUDE_NAMES" ]  && log "EXCLUDE 名单:  $WATCHDOG_EXCLUDE_NAMES"
[ -n "$WATCHDOG_AUTOHEAL_NAMES" ] && log "autoheal 名单: $WATCHDOG_AUTOHEAL_NAMES"
[ -n "$WATCHDOG_MONITOR_NAMES" ]  && log "monitor 名单:  $WATCHDOG_MONITOR_NAMES"
log "label 键: $LABEL_KEY (容器加 --label ${LABEL_KEY}=autoheal 或 monitor 启用)"

LAST_ROTATE=$(date +%s)

# ---------- 主循环 ----------
while true; do
    # Docker 守护进程不可用时跳过本轮
    if ! docker ps >/dev/null 2>&1; then
        log "警告: Docker 守护进程不可用, 跳过本轮"
        sleep "$CHECK_INTERVAL"
        continue
    fi

    unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "{{.ID}}" 2>/dev/null || true)

    if [ -n "$unhealthy_containers" ]; then
        container_count=$(echo "$unhealthy_containers" | wc -l | tr -d '[:space:]')
        log "检测到 $container_count 个不健康容器"
        while read -r cid; do
            [ -n "$cid" ] && process_container "$cid"
        done <<< "$unhealthy_containers"
    fi

    # 重置健康容器的失败计数
    reset_healthy_container_counters

    # 每天清理一次过期日志
    now=$(date +%s)
    if [ "$((now - LAST_ROTATE))" -ge 86400 ]; then
        rotate_logs
        LAST_ROTATE=$now
    fi

    sleep "$CHECK_INTERVAL"
done
