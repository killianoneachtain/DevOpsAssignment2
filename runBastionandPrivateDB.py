#!/usr/bin/env python3
import os
import boto3
import botocore
import subprocess
import awscli

import sys
import time
from datetime import datetime, timedelta
from colorama import Fore, Back, Style 

import menus

ec2 = boto3.resource('ec2')
s3 = boto3.resource("s3")
cloudwatch = boto3.resource('cloudwatch')
alarm = cloudwatch.Alarm('name')
vpc = ec2.Vpc('vpc-01d5cd1df29c740a1')

instanceID=''

# user data for creating instance, to update yum and install apache server framework
server_user_data = '''#!/bin/bash
echo -e "[mongodb-org-4.2]\nname=MongoDB Repository\nbaseurl=https://repo.mongodb.org/yum/amazon/2013.03/mongodb-org/4.2/x86_64/\ngpgcheck=1\nenabled=1\ngpgkey=https://www.mongodb.org/static/pgp/server-4.2.asc" > /etc/yum.repos.d/mongodb-org-4.2.repo
'''

# su - ec2-user -c 'cd walkway-AWS; node index.js' 

#----------------------------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------------------------

# Create instances in VPC / Subnet / Security Group

def create_instance(InstanceType, VpcId, SubnetId, SecurityGroupId, InstanceName, keypair):						
		try:		
				tags = {}
				nametag={('Key', "Name"), ('Value', InstanceName),}											
				tags.update(nametag)				
		except Exception as error:
				print (error)		

		if InstanceName == 'Walkway-MongoDB-Server':
				try:
						instance = ec2.create_instances(			
							ImageId=get_AMI_ID(), 
							KeyName=keypair,
							MinCount=1,
							MaxCount=1,
							InstanceType=InstanceType,
							Monitoring={
								'Enabled' : True
							},
							UserData=server_user_data,
							SubnetId = SubnetId,	
							SecurityGroupIds=[SecurityGroupId],
							PrivateIpAddress='10.0.3.66',
							)
				except Exception as error:
						print (error)
		
		else:
				try:		
						instance = ec2.create_instances(			
							ImageId=get_AMI_ID(), 
							KeyName=keypair,
							MinCount=1,
							MaxCount=1,
							InstanceType=InstanceType,
							Monitoring={
								'Enabled' : True
							},
							SubnetId = SubnetId,	
							SecurityGroupIds=[SecurityGroupId]
							)
				except Exception as error:
						print (error)

		instanceId = instance[0].id
		print (Fore.YELLOW + "\n\n\t%s Instance ID is : " % (str(InstanceName)), instanceId)
		instance = ec2.Instance(instanceId)
		ec2.create_tags(Resources=[instanceId], Tags=[tags],)

		print (Fore.WHITE + "\n\n\tWaiting for Instance to begin 'running'. \n\tPlease Allow 30 seconds.")

		instance.wait_until_running(
				Filters=[
					{
						'Name': 'instance-id', 
						'Values': [ instanceId ]
		 			}
				],
				DryRun=False,		
		)


		print (Fore.GREEN + "\n\tInstance Status : \tRUNNING")


		keyName = instance.key_name
		instanceIP = instance.public_ip_address
		privateIP = instance.private_ip_address


		#------- Status Checking Routine -------------------------------------------------
		# We will not proceed to SSH into the instance until the Status Checks
		# are complete and both have been passed.
		#---------------------------------------------------------------------------------

		print (Fore.WHITE + "\n\n\tWaiting for AWS Status Checks to Pass...\n\n")

		status_check_cmd = 'aws ec2 describe-instance-status --instance-id %s | egrep \'ok|passed\' | wc -l' % (instanceId)

		checkCount = ""

		while checkCount != "b\'4\\n\'" :
				try:
						process = subprocess.run(status_check_cmd, shell=True, stdout=subprocess.PIPE, stderr= subprocess.PIPE)
						output = str(process.stdout)			
						if output == "b\'4\\n\'":				
							print ("\n2/2 AWS Checks Have Passed.\n\n")
							break
				except Exception as error:
						print (error)		

		# ---------- Reload instance and redefine variable ---------------------------

		instance.reload()

		keyName = instance.key_name
		publicIP = instance.public_ip_address
		privateIP = instance.private_ip_address
		instanceID = instance.id
		print ("INSTANCE ID IS : ",instance.id)
		print ("Public IP address is : ", instanceIP)
		return [instanceID, publicIP, privateIP]


# This will log into the MongoDB Private Instance via the Bastion, and install and run a MongoDB server.
def start_MongoDB_server(keypair, bastionPublicIP,serverPrivateIP):		
		serverPath = "ssh -i %s -A ec2-user@%s 'ssh -A ec2-user@%s \'" % (keypair, bastionPublicIP,serverPrivateIP)

		# order of work : 
		#ssh-add -k kon_keypair.pem
		#ssh-add -L
		#ssh -i kon_keypair.pem -A ec2-user@<BastionPublicIP>
		#ssh -A ec2-user@10.0.3.66 'sudo touch /etc/yum.repos.d/mongodb-org-4.2.repo'
#ssh -A ec2-user@10.0.3.66 'sudo chmod 777 /etc/yum.repos.d/mongodb-org-4.2.repo'
#ssh -A ec2-user@10.0.3.66 'sudo echo "[mongodb-org-4.2]\nname=MongoDB Repository\nbaseurl=https://repo.mongodb.org/yum/amazon/2013.03/mongodb-org/4.2/x86_64/\ngpgcheck=1\nenabled=1\ngpgkey=https://www.mongodb.org/static/pgp/server-4.2.asc" > /etc/yum.repos.d/mongodb-org-4.2.repo'
		#sudo yum install -y mongodb-org
		#mkdir db
		#sudo mongod -dbpath db --bind_ip_all

		cmdList = ["ssh-add -k %s" % (keypair), "%smkdir -p /etc/yum.repos.d\'\'" % (serverPath), "ssh-add -L" ,"%ssudo touch /etc/yum.repos.d/mongodb-org-4.2.repo\'\'" % (serverPath), "%ssudo chmod 777 /etc/yum.repos.d/mongodb-org-4.2.repo\'\'" % (serverPath), "%ssudo echo $\"[mongodb-org-4.2]\nname=MongoDB Repository\nbaseurl=https://repo.mongodb.org/yum/amazon/2013.03/mongodb-org/4.2/x86_64/\ngpgcheck=1\nenabled=1\ngpgkey=https://www.mongodb.org/static/pgp/server-4.2.asc\" > /etc/yum.repos.d/mongodb-org-4.2.repo\'\'" % (serverPath), "%ssudo yum install -y mongodb-org\'\'" % (serverPath), "%smkdir -p db\'\'" % (serverPath), "%ssudo mongod -dbpath db --bind_ip_all\'\'" % (serverPath)]

		for index in range(len(cmdList)):
				try:	
						print (Fore.CYAN + "\nSubprocess is : " + cmdList[index] )
						result = subprocess.run(cmdList[index] , shell=True, stdout=subprocess.PIPE)
						if result.returncode == 0:
								print (Fore.GREEN + "\n\tSuccessfully executed")						
				except Exception as error:
						print (Fore.RED + error)

# Function to get user account number
def get_User_Id():
		try:
				response = subprocess.run('aws iam get-user', shell=True, stdout=subprocess.PIPE)				
				user = response.stdout.decode("utf-8") 				
				user_start = user.find('iam::') + 5				
				user_end = user_start + 23				
				user_id = user[user_start:user_end:1]

				return user_id
				
		except Exception as error:
				print (error)

# Function to get latest AMI for Linux Instance on AWS
def get_AMI_ID():	
		AMI_ID = ""
		try:
				response = subprocess.run('aws ssm get-parameters --names /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2 --region eu-west-1', shell=True, stdout=subprocess.PIPE)
				#print (response)
				AMI = response.stdout.decode("utf-8") 				
				#print (AMI)
				ami_start = AMI.find('Value') + 9
				#print (ami_start)
				ami_end = ami_start + 21 #ami-04d5cc9b88f9d1d39
				#print(ami_end)
				AMI_ID = AMI[ami_start:ami_end:1]
				return AMI_ID
		
		except Exception as error:
				print (error)


#------------------- Function END -------------------------------------------------------------------------


#------------------- Program Start ------------------------------------------------------------------------

try:
		print(Fore.YELLOW + Style.BRIGHT + """\n\t\t------------ Welcome ------------\n
		Welcome to My Program which will start an AWS EC2 Instance running a Node.js Web Application.		
		You will be asked for information along the way.\n		
		""")		
		use_key=input(Fore.GREEN + "\n\tWould you like to use a Key Pair for your instance(Recommended)? (Y/n)\t")
		if use_key == 'Y' or use_key == 'y':				
				keypair = menus.keypair_menu()				
except Exception as error:
		print (error)

		
print (Fore.GREEN +"\n\n\tKEY PAIR IS : ",keypair)


# Launch the Bastion Server Here
# Save the ip address as 

try:
		bastion = create_instance('t2.nano', 'vpc-01d5cd1df29c740a1', 'subnet-0658cf1b0634849b8', 'sg-0d6f4366e72e023d3', 'Bastion Server', keypair)
		print ("\nThe Bastion's Instance ID is : ", bastion[0], "\n")
		print ("\nThe Bastion's Public IP is : ", bastion[1], "\n")
except Exception as error:
		print (error)

try:
		dbServer = create_instance('t2.nano', 'vpc-01d5cd1df29c740a1', 'subnet-0b9532d89c0b84eec', 'sg-00d2353496f166b2b', 'Walkway-MongoDB-Server', keypair)
		print ("\nThe Private Web-Server's Private IP is : ", dbServer[2], "\n")
except Exception as error:
		print (error)














