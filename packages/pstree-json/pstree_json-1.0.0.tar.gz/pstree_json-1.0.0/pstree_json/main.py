import argparse
import json
import sys
import psutil
from datetime import datetime

PARSER = argparse.ArgumentParser(description='Output linux / mac process tree in JSON.')
PARSER.add_argument('pid', nargs='?', type=int, default=None, help="Root PID to start from (default: PID 1)")
PARSER.add_argument('--ppid', action='store_true', default=False, help="Include parent pid")
PARSER.add_argument("--depth", type=int, help="Truncate to a certain depth")
PARSER.add_argument('--cwd', action='store_true', default=False, help="Include current directory")
PARSER.add_argument('--username', action='store_true', default=False, help="Include username")
PARSER.add_argument('--uid', action='store_true', default=False, help="Include (real) user id")
PARSER.add_argument('--euid', action='store_true', default=False, help="Include effective user id")
PARSER.add_argument('--suid', action='store_true', default=False, help="Include saved user id")
PARSER.add_argument('--guid', action='store_true', default=False, help="Include (real) group id")
PARSER.add_argument('--eguid', action='store_true', default=False, help="Include effective group id")
PARSER.add_argument('--sguid', action='store_true', default=False, help="Include saved group id")
PARSER.add_argument('--nice', action='store_true', default=False, help="Include the cpu nice level")
PARSER.add_argument('--ionice', action='store_true', default=False, help="Include the io nice level")
PARSER.add_argument('--nfd', action='store_true', default=False, help="Include the number of file descriptors")
PARSER.add_argument('--nthreads', action='store_true', default=False, help="Include the number of threads")
PARSER.add_argument('--all', action='store_true', default=False, help="Include all information")

def main():
    args = PARSER.parse_args()
    
    # Get root process - either from argument or default to PID 1
    if args.pid:
        try:
            root = psutil.Process(args.pid)
        except psutil.NoSuchProcess:
            print(f"Error: No process with PID {args.pid}", file=sys.stderr)
            sys.exit(1)
        except psutil.AccessDenied:
            print(f"Error: Permission denied for PID {args.pid}", file=sys.stderr)
            sys.exit(1)
    else:
        # Default to PID 1 (init/systemd)
        root = next(psutil.process_iter())
    
    def info(p):
        data = {}
        try:
            # Always include start time
            start_timestamp = p.create_time()
            data["start_time"] = datetime.fromtimestamp(start_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            data["start_timestamp"] = start_timestamp
            
            if args.all or args.ppid:
                data["ppid"] = p.ppid()
            if args.all or args.cwd:
                data["cwd"] = p.cwd()
            if args.all or args.username:
                data["username"] = p.username()
            if args.all or args.uid:
                data["uid"] = p.uids()[0]
            if args.all or args.euid:
                data["euid"] = p.uids()[1]
            if args.all or args.suid:
                data["suid"] = p.uids()[2]
            if args.all or args.uid:
                data["gid"] = p.gids()[0]
            if args.all or args.euid:
                data["egid"] = p.gids()[1]
            if args.all or args.suid:
                data["sgid"] = p.gids()[2]
            if args.all or args.nice:
                data["nice"] = p.nice()
            if args.all or args.ionice:
                data["ionice"] = p.ionice()
            if args.all or args.nfd:
                data["nfd"] = p.num_fds()
            if args.all or args.nthreads:
                data["nthreads"] = p.num_threads()
        except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess):
            # Process disappeared or is inaccessible
            pass
        return data
    
    print(json.dumps(create_tree(root, info, depth=args.depth), indent=4))

def create_tree(p, info, depth):
    # Calculate next depth
    if depth is None:
        next_depth = None
    else:
        next_depth = depth - 1
    
    # Try to get process info, handle zombies and permission errors
    try:
        argv = p.cmdline()
        extra_info = info(p)
    except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess):
        # For zombie/inaccessible processes, use minimal info
        try:
            argv = [f"<{p.name()}>"]
        except:
            argv = ["<unknown>"]
        extra_info = {}
    
    # Only include children if depth allows
    if depth is None or depth > 0:
        children = []
        for c in p.children():
            try:
                children.append(create_tree(c, info, next_depth))
            except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess):
                # Skip children we can't access
                pass
    else:
        children = []
    
    # Get number of children safely
    try:
        nchildren = len(p.children())
    except:
        nchildren = 0
    
    return dict(
        pid=p.pid,
        argv=argv,
        children=children,
        nchildren=nchildren,
        **extra_info)