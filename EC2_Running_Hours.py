import boto3
import argparse
import sys
import os
import botocore
from datetime import timedelta, datetime, timezone

def parse_arg():
  parser = argparse.ArgumentParser()
  parser.add_argument('--profile', help="Provide the aws profile name", required=True)
  parser.add_argument('--region', help="Region of the AWS resource", default='us-east-1')
  return parser.parse_args()

def fopen(profile, region, service):
  x = datetime.now()
  fname = service + '/' + profile + '_' + service + '_' + region + '_' + x.strftime("%d%b%y") + '.txt'
  if not os.path.exists(os.path.dirname(fname)):
    try:
      os.makedirs(os.path.dirname(fname))
    except OSError as exc: # Guard against race condition
      if exc.errno != errno.EEXIST:
        raise
  return open(fname,"w")

def session_create(profile, region, service):
  session = boto3.Session(profile_name=profile, region_name=region)
  return session.client(service)

if __name__ == '__main__':
  args        = parse_arg()
  profile     = args.profile
  region      = args.region
  ec2data     = fopen(profile, region, 'ec2data')
  ec2         = session_create(profile, region, 'ec2')
  separator   = "^"
  Headers     = ["SrNo", "Acc Name", "Region", "InstanceID", "InstName", "State", "Instance Type", "OS", "Inst Launch Time", "Total_RunningHours", "MTD_RunningHours" ]
  H = separator.join(Headers)
  print(H, file=ec2data)
  print("{}, {}".format(profile, region))
  count = 0
  paginator = ec2.get_paginator('describe_instances')
  response_iterator = paginator.paginate()

  for page in response_iterator:
    eccdata = {}
    cnt = 0
    for data in page['Reservations']:
      #print("-- {} --".format(data['Instances']))
      for h in Headers:
        eccdata[h] = 'NA'
      cnt                         = cnt + 1
      ie                          = data['Instances'][0]
      eccdata['SrNo']             = cnt
      eccdata['Acc Name']         = profile
      eccdata['Region']           = region
      eccdata['InstanceID']       = ie.get('InstanceId')
      eccdata['State']            = ie.get('State').get('Name')
      eccdata['Instance Type']    = ie.get('InstanceType')
      eccdata['OS']               = ie.get('Platform')
      eccdata['Inst Launch Time'] = ie.get('LaunchTime')
      Tags                        = ie.get('Tags')
      input_date_str              = str(ie.get('LaunchTime'))
      # Convert the input date string to a datetime object
      input_date = datetime.fromisoformat(input_date_str)

      # Get the current date and time in UTC
      current_date = datetime.now(timezone.utc)

      # Calculate the time difference in hours
      time_difference = (current_date - input_date).total_seconds() / 3600

      # Calculate the first day of the current month
      first_day_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

      # Calculate the time difference in hours
      mtd_time_difference = (current_date - max(input_date, first_day_of_month)).total_seconds() / 3600

      eccdata['Total_RunningHours']     = round(time_difference,0)
      eccdata['MTD_RunningHours'] = round(mtd_time_difference,0)
      if Tags is not None:
        for t in Tags:
          K = t['Key']
          V = t['Value']
          if K == 'Name': eccdata['InstName'] = V
      rowtup = []
      for h in Headers:
        rowtup.append(eccdata[h])
      row = separator.join(map(str, rowtup))
      print(row, file=ec2data)
