#!/usr/bin/env python3
import argparse
import re
import sys
import pprint
import logging
from ns1 import NS1, Config


#class Robot:
#    pass

#if __name__ == "__main__":

parser = argparse.ArgumentParser(
    description='Update CDN records in NS1 to migrate from CloudFront to CloudFlare')
parser.add_argument("-k", "--key", type=str, help='NS1 API key', required=True)
parser.add_argument("-c", "--cname", type=str,
                    help='Source CNAME record', required=True)
parser.add_argument("-v", "--verbosity", type=int, default=0,
                    help='verbosity level (0-5)', required=False)
parser.print_usage
args = parser.parse_args()
cname = args.cname.lower() if re.match(r'^[a-z0-9\-]+\.tango\.me$', args.cname,
                                       re.IGNORECASE) else parser.exit(message="Error! Wrong CNAME value!\n", status=1)
config = Config()
config.createFromAPIKey(args.key)
config['verbosity'] = args.verbosity
if config['verbosity'] > 0:
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%H:%M:%S',)
    print(config)
api = NS1(config=config)

rec = api.loadRecord(cname, 'CNAME')
print(rec, file=sys.stderr)

# you can access all the record information via the data property
# pprint.pprint(rec.data)

answers = rec.data["answers"]
pprint.pprint(answers)
if (len(answers) < 1 and len(answers) > 2):
    raise Exception(
        "There are too many values for the record " + rec["domain"])
for answer in answers:
    vHosts = answer.get('answer')
    if (not vHosts or (len(vHosts) != 1)):
        raise Exception("There are too many values in an answer " +
                        vHosts + " for the record " + rec["domain"])
    vHost = vHosts[0]
    if re.search(r'^[a-z0-9\-]+\.cloudfront\.net\.$', vHost, re.IGNORECASE):
        print("CloudFront: " + str(vHost))
        weight = answer.get('meta').get('weight') if answer.get('meta') else None
        if weight is None or not re.match(r'^\d+\.*\d*$',weight):
            # TODO: Add a filter configuration and a weight to the record?
    #        rec.update(filters=[{'weighted_shuffle': {}},
    #                            {'select_first_n': {'N': 1}}]
    #                   )
            print("Weight hasn't been found or has incorrect format in the answer " + str(answer))
            rec.update(answers='6.6.6.6')
    #        rec.update(filters=[{'geotarget_country': {}},
    #                            {'select_first_n': {'N': 1}}],
    #                            ttl=10)
            rec.reload();
            weight = answer.get('meta').get('weight') if answer.get('meta').get('weight') is not None else exit()
#            raise Exception("Weight hasn't been found in the answer")
        else:
            print("Weight is " + str(weight) + str(answer))
    elif re.search(r'^[a-z0-9\-]+\.cloudflare\.net\.$', vHost, re.IGNORECASE):
        print("CloudFlare: " + str(vHost))
        print(answer['meta']['weight'])
    else:
        print(vHost)
        raise Exception("vHost " + str(vHost) + " is neither CloudFront or CloudFlare")



'''
# set filters
rec.update(filters=[{'weighted_shuffle': {}},
                    {'select_first_n': {'N': 1}}]
           )

print(rec.data['answers'])
rec.update(answers=[{'answer': ['1.1.1.1'],
                     'meta': {
                         'up': True,
                         'country': ['US']
                         }
                     },
                    {'answer': ['9.9.9.9'],
                     'meta': {
                         'up': False,
                         'country': ['FR']
                         }
                     }])
print(rec.data['answers'])
'''
# record usage
print(rec.qps())
