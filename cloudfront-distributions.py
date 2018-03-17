#!/usr/bin/env python3

import boto3
import re
import argparse
import pprint

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')




client = boto3.client('cloudfront')
dl = client.list_distributions()

parser = argparse.ArgumentParser(
    description='Return first alias name of CloudFront distribution name.')
parser.add_argument("-d", "--distribution", type=str, help='Distribution name, for example, "http://dzabcdefgh.cloudfront.net"', required=False)
parser.add_argument("-v", "--verbose", type=str2bool, nargs='?',
                        const=True, default=False, metavar='yes|NO',
                        help="Return extended details about distribution")
parser.print_help()

print("")
args = parser.parse_args()
name = args.distribution.lower() if args.distribution and len(args.distribution) > 12 else None
verbose = args.verbose if args.verbose else None
pp = pprint.PrettyPrinter(indent=4) if verbose else None


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
            pprint.pprint(dist) if verbose else None
            found += 1
    if found < 1:
        print("Not found :-(")
    elif found > 1:
        print("Too many distributions found, specify longer domain name, please")
    name = None