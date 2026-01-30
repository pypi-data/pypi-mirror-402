import sys
import urllib.request
import urllib.parse
import threading

class Guardian:
    SERVER_URL = "http://localhost:8080/event"

    @staticmethod
    def init():
        # 자바의 UncaughtExceptionHandler 역할
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # Ctrl+C 같은 건 무시
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # 에러 로그 출력 후 서버에 전송
            print(f"Error Caught: {exc_value}")
            Guardian.send_signal("ERROR")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

        sys.excepthook = handle_exception

    @staticmethod
    def success():
        Guardian.send_signal("SUCCESS")

    @staticmethod
    def arrive(text):
        Guardian.send_signal("ARRIVE", text)

    @staticmethod
    def send_signal(signal_type, message=""):
        def task():
            try:
                params = {"type": signal_type}
                if message:
                    params["msg"] = message
                
                # 파이썬의 urlencode는 자바보다 훨씬 편하다 게이야
                query_string = urllib.parse.urlencode(params)
                full_url = f"{Guardian.SERVER_URL}?{query_string}"
                
                # 자바에서 curl 프로세스 빌더 쓴 것처럼 
                # 여기선 별도 스레드에서 비동기로 요청 보냄
                with urllib.request.urlopen(full_url) as response:
                    pass 
            except Exception:
                pass # 서버 꺼져있어도 프로그램은 돌아가야 하니까 무시

        # 메인 로직 방해 안 되게 스레드로 실행 (비동기)
        threading.Thread(target=task, daemon=True).start()
