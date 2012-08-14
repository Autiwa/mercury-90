#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v1.1
# To check if there is NaN in the orbits, or if the simulation did not have time to finish itself before the allowed time by the server.

import os
import pdb
import autiwa
import sys
import subprocess

# Get current working directory
rep_exec = os.getcwd()

#    .-.     .-.     .-.     .-.     .-.     .-.     .-.     .-.     .-. 
#  .'   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   `.
# (    .     .-.     .-.     .-.     .-.     .-.     .-.     .-.     .    )
#  `.   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   .'
#    )    )                                                       (    (
#  ,'   ,'                                                         `.   `.
# (    (                     DEBUT DU PROGRAMME                     )    )
#  `.   `.                                                         .'   .' 
#    )    )                                                       (    (
#  ,'   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   `.
# (    '  _  `-'  _  `-'  _  `-'  _  `-'  _  `-'  _  `-'  _  `-'  _  `    )
#  `.   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   .'
#    `-'     `-'     `-'     `-'     `-'     `-'     `-'     `-'     `-'

isRestart = False # Say if we want to re-run the simulation or not.
isMeta = False # If we consider the current folder as a folder that list sub-meta-simulations where the simulations really are
isContinue = False # Do we want to continue simulations that did not have time to finish?

isProblem = False
problem_message = "The script can take various arguments :" + "\n" + \
"(no spaces between the key and the values, only separated by '=')" + "\n" + \
" * help : display a little help message on HOW to use various options" + "\n" + \
" * meta : option that will consider the current folder as a folder that list meta simulation instead of simple simulations" + "\n" + \
" * continue : Say that we want to continue the simulations that did not have enough time to finish" + "\n" + \
" * restart : Say if we want to re-run the simulation in case of NaN problems" + "\n" + \
"" + "\n" + \
"Example : mercury-check-simulation.py meta restart continue"

# We get arguments from the script
for arg in sys.argv[1:]:
  try:
    (key, value) = arg.split("=")
  except:
    key = arg
  if (key == 'restart'):
    isRestart = True
  elif (key == 'continue'):
    isContinue = True
  elif (key == 'meta'):
    isMeta = True
  elif (key == 'help'):
    isProblem = True
  else:
    print("the key '"+key+"' does not match")
    isProblem = True

if isProblem:
  print(problem_message)
  exit()


# We go in each sub folder of the current working directory

# If sub folders are meta simulation folders instead of folders, we list the meta simulation folder to run the test in each sub folder.
if (isMeta):
  meta_list = [dir for dir in os.listdir(".") if (os.path.isdir(dir))]
  meta_list.sort()
else:
  meta_list = ["."]


for meta in meta_list:
  os.chdir(meta)
  
  if (meta == '.'):
    absolute_parent_path = rep_exec
  else:
    absolute_parent_path = os.path.join(rep_exec, meta)
  
  # We get the list of simulations
  simu_list = [dir for dir in os.listdir(".") if (os.path.isdir(dir))]
  #autiwa.suppr_dossier(liste_simu,dossier_suppr)
  simu_list.sort()
  
  # We check which folders contain NaN
  (stdout, stderr, returnCode) = autiwa.lancer_commande('grep -l "NaN" */big.dmp')
  if (returnCode == 0):
    NaN_folder = stdout.split("/big.dmp\n")
    NaN_folder.remove('') # we remove an extra element that doesn't mean anything
  else:
    NaN_folder = []

  for simu in simu_list:
    os.chdir(simu)
    
    if not(os.path.isfile("param.in")):
      print("%s/%s : doesn't look like a regular simulation folder" % (absolute_parent_path, simu))
      print("\t 'param.in' does not exist, folder skipped")
      os.chdir("..")
      continue
    
    # We check if the simulation had time to finish
    command = 'tail info.out|grep "Integration complete"|wc -l'
    (stdout, stderr, returnCode) = autiwa.lancer_commande(command)
    if (returnCode != 0):
      print("The command '%s' did not end correctly" % command)
      print(stderr)
      pdb.set_trace()
    is_finished = int(stdout.split("\n")[0]) # We get the number of times "Integration complete" is present in the end of the 'info.out' file
    
    # If there is Nan, we do not want to continue the simulation, but restart it, or check manually, so theses two kinds of problems are separated.
    if simu not in NaN_folder:
      if (is_finished == 0):
        print("%s/%s : The simulation is not finished" % (absolute_parent_path, simu))
        if (isContinue):
          command = "rm *.aei *.clo"
          print("\tCleaning the simulation files : %s" % command)
          (stdout, stderr, returnCode) = autiwa.lancer_commande(command)
    
          command = "./runjob"
          print("\tStarting the simulation again : %s" % command)
          job = subprocess.Popen(command, shell=True)
          returnCode = job.wait()
        
    else:
      print("%s/%s : NaN are present" % (absolute_parent_path, simu))
      if (isRestart):
        # For each folder were there is a problem (NaN in the output in other words) we clean and relaunch the simulation
        command = "rm *.out *.dmp *.tmp *.sh.* *.aei *.clo"
        print("\tCleaning the simulation files : %s" % command)
        (stdout, stderr, returnCode) = autiwa.lancer_commande(command)
        
        command = "./runjob"
        print("\tContinuing the simulation to allow it to finish properly : %s" % command)
        job = subprocess.Popen(command, shell=True)
        returnCode = job.wait()
  
    # We get back in the parent directory
    os.chdir("..")
  
  os.chdir(rep_exec)
  
# TODO Check in a folder if a simulation is currently running (don't know how to test that)