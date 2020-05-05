#!/usr/bin/env python3
import os
import boto3
import botocore
import subprocess
import awscli

import sys
from colorama import Fore, Back, Style

import menus 

ec2 = boto3.resource('ec2')

cloudwatch = boto3.resource('cloudwatch')
alarm = cloudwatch.Alarm('name')
client = boto3.client('ec2')

instanceID=''

# user data for creating instance, to install Node app in a Hapi environment
app_user_data = '''#!/bin/bash
su - ec2-user -c 'curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.35.3/install.sh | bash'
su - ec2-user -c '. ~/.nvm/nvm.sh'
su - ec2-user -c 'nvm install 12.16.2'
su - ec2-user -c 'npm install @hapi/hapi'
su - ec2-user -c 'sudo yum install -y git'
su - ec2-user -c 'git clone https://killianoneachtain:MoWax057xx@github.com/killianoneachtain/walkway-AWS.git'
su - ec2-user -c 'cd walkway-AWS; touch .env'
su - ec2-user -c 'cd walkway-AWS; sudo chmod 700 .env'
su - ec2-user -c 'cd walkway-AWS; echo \"cookie_name=walkway\ncookie_password=secretpasswordnotrevealedtoanyone\ndb=mongodb://10.0.3.66/walkways\nname=walkways\nkey=131821699837553\nsecret=I0NmT17m8Mi7jIxeB-6uvxLqgOE\nCLOUDINARY_URL=cloudinary://131821699837553:I0NmT17m8Mi7jIxeB-6uvxLqgOE\ngoogle_maps_API=AIzaSyCVtqxpiDBYuXR2UpaHSAtQsNzErLQ1frc\nmapbox_Walkways=sk.eyJ1Ijoia29uc291bCIsImEiOiJjazhxZW9xcnQwMmhoM3BubDl4b3dkZHBvIn0.u6CGr9IbBHn_60wsq3q3Aw\nmapbox_default=pk.eyJ1Ijoia29uc291bCIsImEiOiJjazhxZWszbjAwMmhtM21wbmx0Zmp2cmEwIn0.NDRbBBymqk5UPFTgMngyOA\" > .env'
su - ec2-user -c 'cd walkway-AWS; sudo chmod 400 .env'
su - ec2-user -c 'cd walkway-AWS; npm install'
'''

#----------------------------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------------------------


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
				#print (Fore.MAGENTA + "\nThe KEY PAIR to be used is : ", keypair)
except Exception as error:
		print (error)

try:
		tags = {}
		nametag={('Key', "Name"), ('Value', "Walkway-AWS-Master"),}												
		tags.update(nametag)				
except Exception as error:
		print (error)
		
print (Fore.RED +"\n\n\tKEY PAIR IS : ",keypair)


try:
		instance = ec2.create_instances(			
			ImageId=get_AMI_ID(), 
			KeyName=keypair,
			MinCount=1,
			MaxCount=1,
			InstanceType='t2.nano',
			Monitoring={
				'Enabled' : True
			},
			SubnetId = 'subnet-0658cf1b0634849b8',	# Walkway-(VPC-)Public Subnet 1		
			SecurityGroupIds=['sg-0d2ccc0e0155f98f0'], # Walkway-WebServerSG (Security Group)
			UserData=app_user_data)
			
		
except Exception as error:
		print (error)

instanceID = instance[0].id
print (Fore.YELLOW + "\n\n\tInstance ID is : ", instanceID)
instance = ec2.Instance(instanceID)

tags = ec2.create_tags(Resources=[instanceID], Tags=[tags],)



print (Fore.WHITE + "\n\n\tWaiting for Instance to begin 'running'. \n\tPlease Allow 30 seconds.")

instance.wait_until_running(
		Filters=[
			{
				'Name': 'instance-id', 
				'Values': [ instanceID ]
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

status_check_cmd = 'aws ec2 describe-instance-status --instance-id %s | egrep \'ok|passed\' | wc -l' % (instanceID)

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

# ---------- Reload instance and redefine variables ---------------------------

instance.reload()

keyName = instance.key_name
instanceIP = instance.public_ip_address
privateIP = instance.private_ip_address
instanceID = instance.id
print ("INSTANCE ID IS : ",instance.id)

# Stop the instance so that the image can be created
try:
		response = client.stop_instances(
			InstanceIds=[
				instanceID,
			],
			Hibernate=False,			
			Force=True
		)
		
except Exception as error:
		print (error)

try:
		instance.wait_until_stopped(
			Filters=[
				{
				    'Name': 'instance-id',
				    'Values': [
				        instanceID,
				    ]
				},
			]			
		)
		print ("\tWaiting for instance to stop, to create Image.")
except Exception as error:
		print (error)



#instance = ec2.Instance(instanceID)
#create an AMI which can be used in Auto Scaling Groups and for Target Groups 
try:
		image = boto3.client('ec2').create_image(InstanceId=instance.id, Description='Master Instance of Walkway App',NoReboot=False, Name="Walkway App")
except Exception as error:
		print (error)
