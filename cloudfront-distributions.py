#!/usr/bin/env python3

import boto3
import re
import argparse

#import pprint
#pp = pprint.PrettyPrinter(indent=4)

parser = argparse.ArgumentParser(
    description='Return first alias name of CloudFront distribution name.')
parser.add_argument("-d", "--distribution", type=str, help='Distribution name, for example, "http://dzabcdefgh.cloudfront.net"', required=False)

parser.print_help()

print("")
args = parser.parse_args()
name = args.distribution.lower() if args.distribution and len(args.distribution) < 12 else None


client = boto3.client('cloudfront')
dl = client.list_distributions()


while True:
    found = 0
    name = name if name else input("Enter distribution name: ")
    n = re.match(r'^\s*(?:http:)*(?://)*(d[a-z0-9]+)\s*\.*.*$', name, re.I|re.VERBOSE)
    if n:
        name = n.group(1)
    else:
        print("Wrong distribution name \"" + name + "\"!")
        break
    regex = r'.*' + re.escape(name) + '.*'
    for dist in dl.get('DistributionList').get('Items'):
        if re.match(regex, dist.get('DomainName'), re.IGNORECASE):
            print(dist.get('DomainName') + " => " + dist.get("Aliases").get('Items')[0])
            found += 1
    if found < 1:
        print("Not found :-(")
    elif found > 1:
        print("Too many distributions found, specify longer domain name, please")
    name = None