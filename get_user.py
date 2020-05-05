#!/usr/bin/env python3
import awscli
import subprocess
import boto3

try:
		response = subprocess.run('aws iam get-user', shell=True, stdout=subprocess.PIPE)
		print (type(response))
		user = response.stdout.decode("utf-8") 
		print (user)
		user_start = user.find('iam::') + 5
		print (user_start)
		user_end = user_start + 12
		print(user_end)
		user_id = user[user_start:user_end:1]
		print ("USER ID IS : ", user_id)
except Exception as error:
		print (error)


