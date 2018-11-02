#!/usr/bin/env python

import geni.portal as portal
import geni.rspec.pg as RSpec
import geni.rspec.igext as IG
# Emulab specific extensions.
import geni.rspec.emulab as emulab
from lxml import etree as ET
import crypt
import random
import os.path
import sys

TBURL = "http://www.emulab.net/downloads/openstack-setup-v33.tar.gz"
TBPERM = "sudo chmod -R 755 /local/repository/*.sh"
TBCMD = "sudo mkdir -p /root/setup && (if [ -d /local/repository ]; then sudo -H /local/repository/setup-driver.sh 2>&1 | sudo tee /root/setup/setup-driver.log; else sudo -H /tmp/setup/setup-driver.sh 2>&1 | sudo tee /root/setup/setup-driver.log; fi)"
IMAGE = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU18-64-STD"

#
# For now, disable the testbed's root ssh key service until we can remove ours.
# It seems to race (rarely) with our startup scripts.
#
disableTestbedRootKeys = True

#
# Create our in-memory model of the RSpec -- the resources we're going to request
# in our experiment, and their configuration.
#
rspec = RSpec.Request()

#
# This geni-lib script is designed to run in the CloudLab Portal.
#
pc = portal.Context()

#
# Define *many* parameters; see the help docs in geni-lib to learn how to modify.
#

pc.defineParameter("seedlabtype","SEED Lab",
                   portal.ParameterType.STRING,"Packet Sniffing and Spoofing",
                   [("packet_sniffing","Packet Sniffing and Spoofing"),
                    ("tcp_ip","TCP/IP Attack"),
                    ("buffer_overflow","Buffer Overflow Vulnerability"),
                    ("return-to-libc","Return-to-Libc Attack"),
                    ("environment-setuid","Environment Variable and Set-UID"),
                    ("csrf","Cross-site Request Forgery"),
                    ("xsf","Cross-site Scripting Attack"),
                    ("sql","SQL Injection Attack")])
pc.defineParameter("studentCount", "Number of students",
                   portal.ParameterType.INTEGER, 1)
pc.defineParameter("raw", "Use physical nodes",
                    portal.ParameterType.BOOLEAN, False)

#
# Get any input parameter values that will override our defaults.
#
params = pc.bindParameters()

#
# Give the library a chance to return nice JSON-formatted exception(s) and/or
# warnings; this might sys.exit().
#
pc.verifyParameters()

tourDescription = \
  "This profile provides a highly-configurable SEED Lab infrastructure"
#
# Setup the Tour info with the above description and instructions.
#  
tour = IG.Tour()
tour.Description(IG.Tour.TEXT,tourDescription)
#tour.Instructions(IG.Tour.MARKDOWN,tourInstructions)
rspec.addTour(tour)

def Node(name, public):
  if params.raw:
    newnode = RSpec.RawPC(name)
  else:
    newnode = geni.rspec.igext.XenVM(name)
    newnode.ram = 2048
    newnode.cores = 2
  if public:
   newnode.routable_control_ip = True
  return newnode                    

# Setup experiments for individual students plus one lab instructor
lan = RSpec.LAN()
rspec.addResource(lan)
prefixForIP = "192.168.1."
local_ip_count = 0                   
for i in range(params.studentCount + 1):
  if params.seedlabtype == "packet_sniffing":
    if i == 0:
      node = Node("instructor", false)
    else:
      node = Node("lab_instance_"+str(i), false)
    node.disk_image = IMAGE
    local_ip_count += 1                    
    iface = node.addInterface("if" + str(local_ip_count))
    iface.component_id = "eth1"
    iface.addAddress(pg.IPv4Address(prefixForIP + str(local_ip_count), "255.255.255.0"))
    link.addInterface(iface)
    rspec.addResource(node)
                    
  # for packet sniffing, we need one target node that would run a netcat listening post and also 
  # run various programs that keep sending packets to the instructor's machine
  if params.seedlabtype == "packet_sniffing":                 
    node = Node("target", false)
    node.disk_image = IMAGE
    local_ip_count += 1
    iface = node.addInterface("if" + str(local_ip_count))
    iface.component_id = "eth1"                    
    iface.addAddress(pg.IPv4Address(prefixForIP + str(local_ip_count), "255.255.255.0"))
    link.addInterface(iface)
                    
pc.printRequestRSpec(rspec)
