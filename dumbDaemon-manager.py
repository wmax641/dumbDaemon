#!/usr/bin/python3

#simple daemon manager for python3. Use to summon and vanquish your own daemons
#
#Basically, perform a double fork and have the grandchild process run the daemon 
#
#Written for python3.4

#
#Forking daemon based off
#  http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
#

import sys, os, signal
import argparse
import time
import pwd



##### Settings (change these): #####

#PID file location. The daemon's process id will be stored here so we can 
#find the process again when we want to kill the daemon
PID_FILE = "/var/run/daemonSpawn.pid"



def main():
   #Check if root user, if not, then exit. We need root privilege to write pid
   #files to /var/run
   if(os.getuid() != 0):
      print("You need to be root to run this")
      sys.exit(0)

   #Read command line arguments
   parser = argparse.ArgumentParser(description='dumbDaemon: A simple daemon manager')
   group = parser.add_mutually_exclusive_group()
   group.add_argument('-start', action='store_true', help="Start daemon")
   group.add_argument('-stop', action='store_true', help="Stop daemon")
    
   args = parser.parse_args()
   if not (args.start or args.stop): 
      parser.error("Please select -start or -stop")

   #Try to lookup any previous saved process IDs
   try:
      with open(PID_FILE) as f:
         pid = int(f.readline().strip())
         if(isinstance(pid, int)):
            if(args.start):
               print("Existing pid file at {} with process ID {}".format(PID_FILE, pid))
               print("You should run -stop before trying to start a new daemon")
               sys.exit(1)
            elif(args.stop):
               stopDaemon(pid)
           
   #PID_FILE was not found
   except FileNotFoundError:
      if(args.start):
         startDaemon()
      elif(args.stop):
         print("Could not find pid file at {}".format(PID_FILE))
         print("Lost track of daemon, if it's running you should manually terminate it")
         sys.exit(1)


def startDaemon():
   print("Starting daemon")

   #Begin forking daemon process, double fork used to completely decouple the daemon 
   #Double forking is normally uneccesary, but we tinfoil hat
   #  read the following for more info:
   #  http://stackoverflow.com/questions/881388/
   try:
      pid = os.fork()
      if(pid > 0):
         #exit first parent
         sys.exit(0)
   except OSError as e:
      sys.stderr.write(e.strerror)
      sys.exit(2)

   #decouple from parent environment
   os.chdir("/")
   os.setsid()
   os.umask(0)
  
   #Second fork
   try:
      pid = os.fork()
      if(pid > 0):
         #exit second parent
         sys.exit(0)
   except OSError as e:
      sys.stderr.write(e.strerror)
      sys.exit(2)

   #write pid to pidfile
   pid = str(os.getpid())
   try:
      with open(PID_FILE, "w") as f:
         f.write("{}\n".format(pid))
   except:
      sys.stderr.write("Could not write pidfile to {}".format(PID_FILE))
      sys.exit(2)

   #redirect standard file descriptors to null, everything after this should go to
   #a log file
   sys.stdout.flush()
   sys.stderr.flush()
   sin = open(os.devnull, "r")
   sout = open(os.devnull, "a+")
   serr = open(os.devnull, "a+")
   os.dup2(sin.fileno(), sys.stdin.fileno()) 
   os.dup2(sout.fileno(), sys.stdout.fileno()) 
   os.dup2(serr.fileno(), sys.stderr.fileno()) 

   #drop privileges(optional)
   try:
      os.setgid(int(pwd.getpwnam("nobody").pw_gid))
      os.setuid(int(pwd.getpwnam("nobody").pw_uid))
   except:
      sys.exit(2)

   #Run daemon
   while(True):
      # Doing work
      time.sleep(2) # Working hard!


def stopDaemon(pid):
   print("Stopping daemon (pid = {})".format(pid))
   os.remove(PID_FILE)
   try:
      os.kill(pid, signal.SIGTERM)
   except:
      pass


if __name__ == '__main__':
   main()

