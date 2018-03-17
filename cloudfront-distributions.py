import boto3
import re
import pprint

pp = pprint.PrettyPrinter(indent=4)
client = boto3.client('cloudfront')
dl = client.list_distributions()

while 1:
    found = 0
    name = input("Enter distribution name: ")
    n = re.match(r'^\s*(?:http:)*(?://)*(d[a-z0-9]+)(?:\.*cloudfront.+)*$', name, re.I)
    if n:
        name = n.group(1)
    regex = r'.*' + re.escape(name) + '.*'
    for dist in dl.get('DistributionList').get('Items'):
        if re.match(regex, dist.get('DomainName'), re.IGNORECASE):
            pp.pprint(dist.get('DomainName'))
            pp.pprint(dist.get("Aliases").get('Items')[0])
            found += 1
            print("")
    if found < 1:
        print("Not found :-(")

# print(list_distributions())
