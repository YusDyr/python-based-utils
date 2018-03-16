#!/usr/bin/env python3

import boto3
# import collections
from datetime import datetime
from datetime import timedelta
import csv
from time import gmtime, strftime

# import smtplib
# from email.MIMEMultipart import MIMEMultipart
# from email.MIMEBase import MIMEBase
# from email.MIMEText import MIMEText
# from email import Encoders
# import os

# Find current owner ID
sts = boto3.client('sts')
identity = sts.get_caller_identity()
ownerId = identity.get('Account')

# Environment Variables
# LIST_SNAPSHOTS_WITHIN_THE_LAST_N_DAYS=os.environ["LIST_SNAPSHOTS_WITHIN_THE_LAST_N_DAYS"]
LIST_SNAPSHOTS_WITHIN_THE_LAST_N_DAYS = 30
# SES_SMTP_USER=os.environ["SES_SMTP_USER"]
# SES_SMTP_PASSWORD=os.environ["SES_SMTP_PASSWORD"]
# S3_INVENTORY_BUCKET=os.environ["S3_INVENTORY_BUCKET"]
# MAIL_FROM=os.environ["MAIL_FROM"]
# MAIL_TO=os.environ["MAIL_TO"]

# Constants
MAIL_SUBJECT = "AWS Inventory for " + ownerId
MAIL_BODY = MAIL_SUBJECT + '\n'

# EC2 connection beginning
ec = boto3.client('ec2')
# S3 connection beginning
s3 = boto3.resource('s3')

# boto3 library ec2 API describe region page
# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_regions
regions = ec.describe_regions().get('Regions', [])
print(regions)
for region in regions:
    reg = region.get('RegionName')
    # get to the curren date
    date_fmt = strftime("%Y_%m_%d", gmtime())
    # Give your file path
    filename = 'AWS_Resources_' + date_fmt + '_' + reg + '.csv'
    csv_file = open(filename, 'w', newline='')
    writer = csv.writer(csv_file, dialect='excel', delimiter=';', quoting=csv.QUOTE_ALL)

    regname = 'REGION :' + reg
    # EC2 connection beginning
    ec2con = boto3.client('ec2', region_name=reg)
    # boto3 library ec2 API describe instance page
    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
    reservations = ec2con.describe_instances().get(
        'Reservations', []
    )
    instances = sum(
        [
            [i for i in r.get('Instances')]
            for r in reservations
        ], [])
    instanceslist = len(instances)
    if instanceslist > 0:
        writer.writerow(['EC2 INSTANCE'] * 7)
        print(['EC2 INSTANCE'] * 7)
        writer.writerow(['InstanceID', 'Instance_State', 'InstanceName',
                         'Instance_Type', 'LaunchTime', 'Instance_Placement',
                         'SecurityGroupsStr'])
        print(['InstanceID', 'Instance_State', 'InstanceName',
                         'Instance_Type', 'LaunchTime', 'Instance_Placement',
                         'SecurityGroupsStr'])
    #
    for instance in instances:
        state = instance.get('State').get('Name')
        Instancename = 'N/A'
        if 'Tags' in instance:
            for tags in instance.get('Tags'):
                key = tags.get('Key')
                if key == 'Name':
                    Instancename = tags.get('Value')
        if state == 'running':
            instanceid = instance.get('InstanceId')
            instancetype = instance.get('InstanceType')
            launchtime = instance.get('LaunchTime')
            Placement = instance.get('Placement').get('AvailabilityZone')
            securityGroups = instance.get('SecurityGroups')
            securityGroupsStr = ''
            for idx, securityGroup in enumerate(securityGroups):
                if idx > 0:
                    securityGroupsStr += '; '
                securityGroupsStr += securityGroup.get('GroupName')
            writer.writerow([instanceid, state, Instancename, instancetype, launchtime, Placement, securityGroupsStr])
            print([instanceid, state, Instancename, instancetype, launchtime, Placement, securityGroupsStr])

    for instance in instances:
        state = instance.get('State').get('Name')
        Instancename = 'N/A'
        if 'Tags' in instance:
            for tags in instance.get('Tags'):
                key = tags.get('Key')
                if key == 'Name':
                    Instancename = tags.get('Value')
        if state == 'stopped':
            instanceid = instance.get('InstanceId')
            instancetype = instance.get('InstanceType')
            launchtime = instance.get('LaunchTime')
            Placement = instance.get('Placement').get('AvailabilityZone')
            writer.writerow([
                instanceid, state, Instancename, instancetype, launchtime, Placement])
            print([
                instanceid, state, Instancename, instancetype, launchtime, Placement])

    # boto3 library ec2 API describe volumes page
    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_volumes
    ec2volumes = ec2con.describe_volumes().get('Volumes', [])
    volumes = sum(
        [
            [i for i in r.get('Attachments')]
            for r in ec2volumes
        ], [])
    volumeslist = len(volumes)
    if volumeslist > 0:
        writer.writerow(['', '', '', ''])
        writer.writerow(['EBS Volume', regname])
        writer.writerow(['VolumeId', 'InstanceId', 'AttachTime', 'State'])

    for volume in volumes:
        VolumeId = volume.get('VolumeId')
        InstanceId = volume.get('InstanceId')
        State = volume.get('State')
        AttachTime = volume.get('AttachTime')
        writer.writerow([VolumeId, InstanceId, AttachTime, State])

    # boto3 library ec2 API describe snapshots page
    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_snapshots
    ec2snapshot = ec2con.describe_snapshots(OwnerIds=[
        ownerId,
    ], ).get('Snapshots', [])

    snapshots_counter = 0
    for snapshot in ec2snapshot:
        snapshot_id = snapshot.get('SnapshotId')
        snapshot_state = snapshot.get('State')
        tz_info = snapshot.get('StartTime').tzinfo
        # Snapshots that were not taken within the last configured days do not qualify for auditing
        timedelta_days = -int(LIST_SNAPSHOTS_WITHIN_THE_LAST_N_DAYS)
        if snapshot.get('StartTime') > datetime.now(tz_info) + timedelta(days=timedelta_days):
            if snapshots_counter == 0:
                writer.writerow(['', '', '', '', ''])
                writer.writerow(['EC2 SNAPSHOT', regname])
                writer.writerow([
                    'SnapshotId', 'VolumeId', 'StartTime', 'VolumeSize', 'Description'])

            snapshots_counter += 1
            SnapshotId = snapshot.get('SnapshotId')
            VolumeId = snapshot.get('VolumeId')
            StartTime = snapshot.get('StartTime')
            VolumeSize = snapshot.get('VolumeSize')
            Description = snapshot.get('Description')
            writer.writerow([
                SnapshotId, VolumeId, StartTime, VolumeSize, Description])

    # boto3 library ec2 API describe addresses page
    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_addresses
    addresses = ec2con.describe_addresses().get('Addresses', [])
    addresseslist = len(addresses)
    if addresseslist > 0:
        writer.writerow(['', '', '', '', ''])
        writer.writerow(['EIPS INSTANCE', regname])
        writer.writerow(['PublicIp', 'AllocationId', 'Domain', 'InstanceId'])

        for address in addresses:
            PublicIp = address.get('PublicIp')
            try:
                AllocationId = address.get('AllocationId')
            except:
                AllocationId = "empty"
            Domain = address.get('Domain')
            if 'InstanceId' in address:
                instanceId = address.get('InstanceId')
            else:
                instanceId = 'empty'
            writer.writerow([PublicIp, AllocationId, Domain, instanceId])


    def printSecGroup(groupType, permission):
        ipProtocol = permission.get('IpProtocol')
        try:
            fromPort = permission.get('FromPort')
        except KeyError:
            fromPort = None
        try:
            toPort = permission.get('ToPort')
        except KeyError:
            toPort = None
        try:
            ipRanges = permission.get('IpRanges')
        except KeyError:
            ipRanges = []
        ipRangesStr = ''
        for idx, ipRange in enumerate(ipRanges):
            if idx > 0:
                ipRangesStr += '; '
            ipRangesStr += ipRange.get('CidrIp')
        writer.writerow([
            groupName, groupType, ipProtocol, fromPort, toPort, ipRangesStr])


    # boto3 library ec2 API describe security groups page
    # http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_security_groups
    securityGroups = ec2con.describe_security_groups(
        Filters=[
            {
                'Name': 'owner-id',
                'Values': [
                    ownerId,
                ]
            }
        ]
    ).get('SecurityGroups')
    if len(securityGroups) > 0:
        writer.writerow(['', '', '', '', ''])
        writer.writerow(['SEC GROUPS', regname])
        writer.writerow([
            'GroupName', 'GroupType', 'IpProtocol', 'FromPort', 'ToPort', 'IpRangesStr'])

        for securityGroup in securityGroups:
            groupName = securityGroup.get('GroupName')
            ipPermissions = securityGroup.get('IpPermissions')
            for ipPermission in ipPermissions:
                groupType = 'ingress'
                printSecGroup(groupType, ipPermission)
            ipPermissionsEgress = securityGroup.get('IpPermissionsEgress')
            for ipPermissionEgress in ipPermissionsEgress:
                groupType = 'egress'
                printSecGroup(groupType, ipPermissionEgress)

    # RDS Connection beginning
    rdscon = boto3.client('rds', region_name=reg)

    # boto3 library RDS API describe db instances page
    # http://boto3.readthedocs.org/en/latest/reference/services/rds.html#RDS.Client.describe_db_instances
    rdb = rdscon.describe_db_instances().get(
        'DBInstances', []
    )
    rdblist = len(rdb)
    if rdblist > 0:
        writer.writerow(['', '', '', ''])
        writer.writerow(['RDS INSTANCE', regname])
        writer.writerow([
            'DBInstanceIdentifier', 'DBInstanceStatus', 'DBName', 'DBInstanceClass'])

    for dbinstance in rdb:
        DBInstanceIdentifier = dbinstance.get('DBInstanceIdentifier')
        DBInstanceClass = dbinstance.get('DBInstanceClass')
        DBInstanceStatus = dbinstance.get('DBInstanceStatus')
        try:
            DBName = dbinstance.get('DBName')
        except:
            DBName = "empty"
        writer.writerow([
            DBInstanceIdentifier, DBInstanceStatus, DBName, DBInstanceClass])

    # ELB connection beginning
    elbcon = boto3.client('elb', region_name=reg)

    # boto3 library ELB API describe db instances page
    # http://boto3.readthedocs.org/en/latest/reference/services/elb.html#ElasticLoadBalancing.Client.describe_load_balancers
    loadbalancer = elbcon.describe_load_balancers().get('LoadBalancerDescriptions', [])
    loadbalancerlist = len(loadbalancer)
    if loadbalancerlist > 0:
        writer.writerow(['ELB INSTANCE', regname])
        writer.writerow(['LoadBalancerName', 'DNSName',
                         'CanonicalHostedZoneName', 'CanonicalHostedZoneNameID'])

    for load in loadbalancer:
        LoadBalancerName = load.get('LoadBalancerName')
        DNSName = load.get('DNSName')
        CanonicalHostedZoneName = load.get('CanonicalHostedZoneName')
        CanonicalHostedZoneNameID = load.get('CanonicalHostedZoneNameID')
        writer.writerow([
            LoadBalancerName, DNSName, CanonicalHostedZoneName, CanonicalHostedZoneNameID])

    # IAM connection beginning
    iam = boto3.client('iam', region_name=reg)

    # boto3 library IAM API
    # http://boto3.readthedocs.io/en/latest/reference/services/iam.html
    writer.writerow(['', '', '', ''])
    writer.writerow(['IAM', regname])
    writer.writerow(['User', 'Policies'])

    users = iam.list_users().get('Users')
    for user in users:
        user_name = user.get('UserName')
        policies = ''
        user_policies = iam.list_user_policies(
            UserName=user_name)["PolicyNames"]
        for user_policy in user_policies:
            if len(policies) > 0:
                policies += ";"
            policies += user_policy
        attached_user_policies = iam.list_attached_user_policies(UserName=user_name)[
            "AttachedPolicies"]
        for attached_user_policy in attached_user_policies:
            if len(policies) > 0:
                policies += ";"
            policies += attached_user_policy.get('PolicyName')
#        writer.writerow([user_name, policies])
