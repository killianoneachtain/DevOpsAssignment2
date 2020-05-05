#!/usr/bin/env python3
import os
import boto3
import botocore
import awscli

ec2 = boto3.resource('ec2')
s3 = boto3.resource("s3")
client = boto3.client('ec2')

vpc = ec2.Vpc('vpc-01d5cd1df29c740a1') #Walkway VPC

subnet = ec2.Subnet('subnet-0b9532d89c0b84eec') #Private Subnet 1 for Walkway subnet-0b9532d89c0b84eec

route_table = ec2.RouteTable('rtb-0641fcbab22fff3a5') #Private Subnet 1 Route Table ID

#print ("Current Route Table for Private Subnet 1 on Walkway-VPC is : ", route_table.routes)

# global variables
elastic_ip=''
allocationID=''
NATGatewayID=''




# 1. Create a NAT Gateway / ELastic IP in the public subnet 1 and 
#create elastic IP first
try: 
		allocate = client.allocate_address(
			Domain='vpc',
			#Address='10.0.0.50',
			#PublicIpv4Pool='10.0.0.0/24',			
			#CustomerOwnedIpv4Pool='string',
			#DryRun=True
		)		
		elastic_ip = allocate['PublicIp']
		allocationID = allocate['AllocationId']
		print ("\n\tElastic IP is :", elastic_ip)
		print ("\n\tAllocationID is :", allocationID, "\n\n")

except Exception as error:
		print (error)

try:
		print ("\tCreating NAT Gateway with Elastic IP\n")
		response = client.create_nat_gateway(
			AllocationId = allocationID , #Elastic IP Allocation ID
			SubnetId='subnet-0658cf1b0634849b8', #Public Subnet 1		
		)		
		NATGatewayID = response['NatGateway']['NatGatewayId']
		print ("\n\tThe NAT Gateway ID is : ", NATGatewayID,"\n\n")
		#do until State is available
		state=''
		while state != 'available':
				NatState = client.describe_nat_gateways(
					Filters=[
						{
							'Name': 'nat-gateway-id',
							'Values': [
								NATGatewayID,
							]
						},
					],					
					NatGatewayIds=[
						NATGatewayID,
					]				
				)
				#print ("\tHere checking the State: \t",NatState)
				state = NatState['NatGateways'][0]['State']
				#print ("\n\t\tState is : ",state)
		print ("\n\tThe current state of the NAT Gateway is : ", state)
		tags = {}
		nametag={('Key', "Name"), ('Value', 'Walkway-NAT Gateway'),}											
		tags.update(nametag)
		ec2.create_tags(Resources=[NATGatewayID], Tags=[tags],)
		
except Exception as error:
		print (error)

# 2. Add NAT Gateway to the route table 

try: 
		route_table = ec2.RouteTable('rtb-0641fcbab22fff3a5') #Private Subnet 1 Route Table ID
		route = route_table.create_route(
		DestinationCidrBlock='0.0.0.0/0',		
		#DryRun=True,
		NatGatewayId = NATGatewayID #The NAT gateway id of created one		
		)
		print ("\n\tCurrent Route Table for Private Subnet 1 on Walkway-VPC is : ", route_table.routes, "\n")
except Exception as error:
		print (error)

