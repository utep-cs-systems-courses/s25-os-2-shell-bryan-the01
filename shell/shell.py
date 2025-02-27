
import os
import sys
import re

def find_path(process):
    paths = os.getenv("PATH", "").split(":")
    for directory in paths:
        full_path = os.path.join(directory, process)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

def execute_process(process):
    args = process.split()
    if not args:
        return
    #Built-in command
    if args[0] == "cd":
        try:
            os.chdir(args[1] if len(args) > 1 else os.getenv("HOME"))
        except FileNotFoundError:
            print(f"cd: {args[1]}: No such directory found")
        return
    #I/O 
    input_file = None
    output_file = None
    new_args = []

    i = 0
    while i < len(args):
        if args[i] == ">":
            if i + 1 < len(args):
                output_file = args[i + 1]
                i += 1
            else:
                print("Syntax error: missing output file")
                return
        elif args[i] == "<":
            if i + 1 < len(args):
                input_file = args[i + 1]
                i += 1
            else:
                print("Syntax error: missing input file")
                return
        else:
            new_args.append(args[i])
        i += 1

    
    full_path = find_path(new_args[0])
    if full_path is None:
        print(f"{new_args[0]}: command not found")
        return
    
    pid = os.fork()

    # Pipe process
    if "|" in args:
        p_index = args.index("|")
        l_proc = args[:p_index]
        r_proc = args[p_index+1:]

        read_fd, write_fd = os.pipe()

        #left process
        pid1 = os.fork()
        if pid1 == 0:
            os.dup2(write_fd, 1)
            os.close(read_fd) 
            os.close(write_fd)
            #close left child fd
            
            full_path = find_path(l_proc[0])
            if full_path is None:
                print(f"{l_proc[0]}: command not found")
                os._exit(0)
            os.execve(full_path, l_proc, os.environ)

        # right process
        pid2 = os.fork()
        if pid2 == 0:
            os.dup2(read_fd, 0)
            os.close(write_fd)
            os.close(read_fd)
            #right child closes fd
            
            full_path = find_path(r_proc[0])
            if full_path is None:
                print(f"{r_proc[0]}: command not found")
                os._exit(0)
            os.execve(full_path, r_proc, os.environ)

        #back to parent process
        os.close(read_fd)
        os.close(write_fd)
        os.waitpid(pid1, 0)
        os.waitpid(pid2, 0)
        return
    
    #Child process
    if pid == 0:
        try:
            # Handle input
            if input_file:
                fd_in = os.open(input_file, os.O_RDONLY)
                os.dup2(fd_in, 0)
                os.close(fd_in)
                
            # Handle output
            if output_file:
                fd_out = os.open(output_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
                os.dup2(fd_out, 1)
                os.close(fd_out)
                
            os.execve(full_path, args, os.environ)
        except FileNotFoundError:
            print(f"{args[0]}: Invalid command")
        os._exit(1)
    #Parent process
    else:
        os.waitpid(pid, 0)

def main():
    PS1 = os.getenv("PS1", "$ ")
    while True:
        command = input(PS1).strip()
        args = command.split()
        
        if command.lower() == "exit":
            print("Exiting shell")
            break
        if not command:
            continue
        execute_process(command)
        

if __name__ == "__main__":
        main()
