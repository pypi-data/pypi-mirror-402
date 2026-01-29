#demo_file.py   16Dec2025  crs Author
import os
import sys
import signal
import subprocess
import importlib.resources
import datetime

class DemoFile:
    def __init__(self):
        self.processes = []
        self.begin = datetime.datetime.now()
        
    def demo_process(self, demo_name,
                     package_name=None):
        """ Run demo - IDLE window, execution
        :demo_name: program  python file
        :package_name: package name
                    default: not from package
                            simple file
        Example
        pro = subprocess.Popen(cmd,
               stdout=subprocess.PIPE, 
               shell=True, preexec_fn=os.setsid) 
        """
        demo_file = self.sample_to_demo_file(
            demo_name, package_name=package_name)

        cmd = ["python3", "-m", "idlelib", demo_file] # Show file
        process = self.run_proc(cmd)
        self.processes.append(process)
        cmd = ["python3", "-m", "idlelib", "-r", demo_file]  # Run file
        process = self.run_proc(cmd)
        self.processes.append(process)

    def run_proc(self, cmd):
        """  os independant Popen process cmd
        :cmd: cmd list
        """
        if os.name == 'posix':  # 'posix' is used for Unix/Linux/macOS
            # Use os.setsid on Unix systems
            process = subprocess.Popen(cmd, preexec_fn=os.setsid)
        elif os.name == 'nt':   # 'nt' is used for Windows
            # Use creationflags for Windows to create a new process group
            process = subprocess.Popen(cmd,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            process = None
            # Handle other potential OS types or raise an error
            raise NotImplementedError(
                f"os.setsid is not supported"
                f" on the current OS: {os.name}")        
        return process
    
    def sample_to_demo_file(self, sample_name,
                            package_name=None):
        """ Translate sample name to demo file
        :sample_name: sample base name
        :package_name: installed package name
                    default: No package
        """
        if package_name is not None:
            package_traversable = importlib.resources.files(package_name)
            print(f"{package_traversable = }")
            demo_file = {package_traversable/sample_name}
        else:
            demo_file = os.path.abspath(sample_name)
        return demo_file

    def get_active(self):
        """ Return list of all active processes
        :returns: list of active processes
        """
        procs = []
        for process in self.processes:
            if process.poll() is not None:
                procs.append(process)
        return procs
    
    def duration(self):
        """ Processes duration from initial
        execution
        :return: floating point in seconds
        """
        diff = datetime.datetime.now() - self.begin
        return diff.total_seconds()
        
    def wait(self, max_wait=None, display=True):
        """ Wait for processes to terminate
        :max_wait: maximum number of seconds
                default: no maximum - till done
        :display: True - display time/time left
        """
        # Wait for all subprocesses to complete
        while True:
            dur = self.duration()
            if (active_procs := self.get_active()) == 0:
                return

            if display:
                print(f"\rtime: {dur:.2f}")
            if (max_wait is not None
                and  dur >= max_wait):
                return 

    def kill_all(self, wait_max=None):
        """ Kill all running processes
        :max_wait: maximum wait for each process end
                default: wait till each process ends
        """
        for process in self.get_active():
            self.kill_proc(process, wait_max=wait_max)        
            
    def kill_proc(self, process, wait_max=None):
        """ Kill one of processes
        :process: process to kill
        :wait_max: maximum wait  for process ends
        # The os.setsid() is passed in the
        # argument preexec_fn so
        # it's run after the fork()
        # and before  exec() to run the shell.
        """
        process.kill()
        if wait_max is not None:
            while True:
                if process.poll() is None:
                    return process.poll()
    def iptest(self, demo_name, package_name=None):
        self.demo_process(demo_name, package_name=package_name )

if __name__ == '__main__':
    demo_name = "show_spokes.py"
    demo_name = "show_spokes_braille.py"
    package_name = None
    if package_name is None:
        # Get the absolute path of the directory containing the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Change the current working directory to the script's directory
        os.chdir(script_dir)
        demo_name = os.path.abspath(demo_name)
    print(f"demo_name: {demo_name}")
    dF = DemoFile()
    
    dF.iptest(demo_name, package_name=package_name)
    dF.wait(max_wait=3)
    print("Times Up")
    dF.kill_all()
    print("All done")