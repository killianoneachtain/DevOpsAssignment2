#!/usr/bin/env python3
import os
import boto3
import botocore
import subprocess
import awscli

def return_keypairs():

		keypairs = []

		response = subprocess.run('aws ec2 describe-key-pairs --no-dry-run --query \'KeyPairs[*].{Name:KeyName}\'', shell=True, stdout=subprocess.PIPE)				
		 
		keynames = response.stdout.decode("utf-8")
		#print (keynames)
		test_sub = ": \""

		res = [i for i in range(len(keynames)) if keynames.startswith(test_sub, i)] 
		#print (res)

		for i in range(len(res)):
				keyname_start = res[i] + 3	
				keyname_end = res[i] + 50
				user_id = keynames[keyname_start:keyname_end:1]
				keypair_name = user_id.split('\"')		
				keypairs.append(keypair_name[0])

		#print (keypairs)
		return keypairs



