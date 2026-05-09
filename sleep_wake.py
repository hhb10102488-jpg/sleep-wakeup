import subprocess
import time
import os

def get_log_filename():
    """sleep_wake_log(1).txt, (2).txt ... 순서로 새 파일 생성"""
    i = 1
    while True:
        filename = f"sleep_wake_log({i}).txt"
        if not os.path.exists(filename):
            return filename
        i += 1

LOG_FILE = get_log_filename()

def log(msg):
    timestamp = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(timestamp)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(timestamp + "\n")

def adb(cmd):
    try:
        result = subprocess.run(["adb"] + cmd, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError("ADB 명령 응답 없음 (타임아웃)")

def get_devices():
    lines = adb(["devices"]).split("\n")[1:]
    return [l.split("\t")[0] for l in lines if "device" in l and "offline" not in l]

def check_device_alive():
    devices = get_devices()
    if not devices:
        raise RuntimeError("기기 연결이 끊어졌습니다.")

def get_screen_state():
    output = adb(["shell", "dumpsys", "power"])
    if not output:
        raise RuntimeError("기기로부터 응답 없음.")
    return "mWakefulness=Awake" in output

def wake_up():
    check_device_alive()
    if not get_screen_state():
        adb(["shell", "input", "keyevent", "KEYCODE_WAKEUP"])
        time.sleep(0.5)
        adb(["shell", "input", "swipe", "540", "1600", "540", "800"])
        log("화면 켜짐")

def sleep_screen():
    check_device_alive()
    if get_screen_state():
        adb(["shell", "input", "keyevent", "KEYCODE_SLEEP"])
        log("화면 꺼짐")

# ── 시작 ──────────────────────────────────────────────────────

devices = get_devices()
log(f"연결된 기기 수: {len(devices)}개 -> {devices}")

if not devices:
    log("연결된 기기 없음. 에뮬레이터를 먼저 실행하세요.")
    exit()

answer = input("\n5초 간격으로 1분간 sleep/wake 실행할까요? (y/n): ").strip().lower()

if answer != "y":
    log("사용자가 실행을 취소했습니다.")
    exit()

log("시작 - 1분간 5초 간격으로 동작")

end_time = time.time() + 60
toggle = True

try:
    while time.time() < end_time:
        if toggle:
            wake_up()
        else:
            sleep_screen()
        toggle = not toggle
        time.sleep(5)

    log("1분 완료. 정상 종료합니다.")

except RuntimeError as e:
    log(f"[오류] 기기 이상 감지 - {e}")
    log("스크립트를 즉시 중지합니다.")

except KeyboardInterrupt:
    log("사용자가 강제 종료했습니다. (Ctrl+C)")

except Exception as e:
    log(f"[예외] 예상치 못한 오류 - {e}")

finally:
    log(f"로그 파일 위치: {os.path.abspath(LOG_FILE)}")
