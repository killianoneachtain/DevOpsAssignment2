#!/usr/bin/env python3
import os
import boto3
import botocore
import subprocess
import awscli

from colorama import Fore, Back, Style 

ec2 = boto3.resource('ec2')
s3 = boto3.resource("s3")
vpc = ec2.Vpc('vpc-01d5cd1df29c740a1')

instanceID=''

# order of work :
#ssh-add -L
#ssh -i kon_keypair.pem -A ec2-user@<BastionPublicIP>
#sudo yum install -y mongodb-org
#mkdir db
#sudo mongod -dbpath db --bind_ip_all

# This will log into the MongoDB Private Instance via the Bastion, and install and run a MongoDB server.
def start_MongoDB_server(keypair, bastionPublicIP,serverPrivateIP):
		
		serverPath = "ssh -t -o StrictHostKeyChecking=no -i %s -A ec2-user@%s 'ssh -t -o StrictHostKeyChecking=no -A ec2-user@%s \"" % (keypair, bastionPublicIP,serverPrivateIP)

		cmdList = ["ssh-add -k %s" % (keypair),
"ssh-add -L",
"%ssudo yum install -y mongodb-org\"\'" % (serverPath), 
"%smkdir -p db\"\'" % (serverPath), 
"%ssudo mongod -dbpath db --bind_ip_all\"\'" % (serverPath)
]
		index=0
		for index in range(len(cmdList)):
				try:	
						print (Fore.CYAN + "\nSubprocess is : " + cmdList[index] )
						result = subprocess.run(cmdList[index] , shell=True, stdout=subprocess.PIPE)						
						if result.returncode == 0:
								print (Fore.GREEN + "\n\tSuccessfully executed")						
				except Exception as error:
						print (Fore.RED + error)

try:
		start_MongoDB_server('kon_keypair.pem', '3.248.215.180', '10.0.3.66')
except Exception as error:
				print (error)
