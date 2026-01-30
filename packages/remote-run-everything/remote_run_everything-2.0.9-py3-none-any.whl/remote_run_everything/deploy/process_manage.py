import os, signal
import subprocess, sys
class ProcessManage:
    def is_process_running(self,pid):
        import psutil
        try:
            process = psutil.Process(pid)
            # Check if process is still running
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
        except psutil.AccessDenied:
            # Process exists but we don't have permission to access it
            print(f"Access denied to process {pid}")
            return True
    def read_pid_file(self,pidfile):
        if os.path.exists(pidfile):
            with open(pidfile, "rb") as f:
                pid = f.read().decode()
                return pid
        return None

    # 只需要在程序中引入这个函数,启动后会把 os.getpid()存入,然后有了pid,结合psutil,什么都有了
    def write_pid_file(self,pidfile,pid):
        with open(pidfile, "wb") as f:
            s = str(pid).encode()
            f.write(s)

    def kill_by_pid(self,pid):
        try:
            os.kill(int(pid), signal.SIGTERM)
        except Exception as e:
            print("kill err==", e)

    def popen_with_pid(self, workdir,  app):
        os.chdir(workdir)
        process = subprocess.Popen(app, creationflags=subprocess.CREATE_NEW_CONSOLE)
        pid= process.pid
        print("new pid====",pid)
        return pid
        # sys.exit()

    def restart_windows(self):
        os.system("shutdown -t 0 -r -f")


