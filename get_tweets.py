#! /usr/bin/env python

import sys, os
from ConfigParser import ConfigParser, NoSectionError, NoOptionError

class TweetSweeper:
    def __init__(self, config_file, output_dir, verbose=False):
        self.config_file = config_file
        self.output_dir = output_dir
        self.verbose = verbose

    def parse_config(self):
        self.config = ConfigParser()
        self.config.read(self.config_file)
        self.token = self.config.get('auth', 'token')
        self.token_key = self.config.get('auth', 'token_key')
        self.secret = self.config.get('auth', 'secret')
        self.secret_key = self.config.get('auth', 'secret_key')
        self.terms = list()
        for t in self.config.items('terms'):
            self.terms.append(t)

    def get_client(self):
        from twitter import Twitter, OAuth
        return Twitter(
            auth=OAuth(self.token, self.token_key,
                       self.secret, self.secret_key),
            api_version=1.1
            )
    def make_output_dir(self):
       try:
           os.stat(self.output_dir)
       except:
           os.mkdir(self.output_dir)

    def fetch_tweets(self):
        self.parse_config()
        self.make_output_dir()
        t = self.get_client()
        for term in self.terms:
            key = term[0]
            query = term[1]
            sinceid = self.get_sinceid(key)
            next_sinceid = sinceid
            if sinceid is None:
                tweets = t.search.tweets(q=query, result_type='recent',
                                         count=100)
            else:
                tweets = t.search.tweets(q=query, result_type='recent',
                                         count=100, since_id=sinceid)
            (min_id, max_id) = self.process_tweets(tweets)

            prev_min_id = min_id
            
            if next_sinceid is None:
                next_sinceid = max_id
            elif max_id is not None and max_id > next_sinceid:
                next_sinceid = max_id
                
            while True:
                if sinceid is None:
                    tweets = t.search.tweets(q=query, result_type='recent',
                                             count=100, max_id=min_id)
                else:
                    tweets = t.search.tweets(q=query, result_type='recent',
                                             count=100, max_id=min_id,
                                             since_id = sinceid)
                (min_id, max_id) = self.process_tweets(tweets)

                if max_id > next_sinceid:
                    next_sinceid = max_id
                        
                if min_id < prev_min_id:
                    prev_min_id = min_id
                else:
                    break

            if next_sinceid is not None:
                self.set_sinceid(key, next_sinceid)


    def process_tweets(self, tweets):
        import simplejson as json
        import codecs
        min_id = None
        max_id = None
        for tweet in tweets['statuses']:
            if min_id is None or tweet['id'] < min_id:
                min_id = tweet['id']
            if max_id is None or tweet['id'] > max_id:
                max_id = tweet['id']
            if self.verbose:
                print("Tweeet: id : %s at %s by name %s text: %s"
                      %(tweet['id'],tweet['created_at'],
                        tweet['user']['screen_name'],
                        tweet['text']))
            tweet_file = os.path.join(self.output_dir,
                                      "%s.json"%(tweet['id']))
            if self.verbose:
                print("save to %s" % tweet_file)

            with codecs.open(tweet_file, 'w', encoding="utf-8") as out:
                out.write(json.dumps(tweet, ensure_ascii=False))
                out.flush()
        return (min_id, max_id)

    def get_sinceid(self, key):
        try:
            return self.config.getint('sinceid', key)
        except (NoSectionError, NoOptionError):
            return None

    def set_sinceid(self, key, next_sinceid):
        if not self.config.has_section('sinceid'):
            self.config.add_section('sinceid')

        if self.verbose:
            print "updating since_id for %s to %s" % (key, next_sinceid)

        self.config.set('sinceid', key, next_sinceid)
        with open(self.config_file, 'wb') as configfile:
            self.config.write(configfile)


def parse_args():
    from optparse import OptionParser
    basedir = os.path.realpath(os.path.dirname(sys.argv[0]))
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config_file",
                      help="configuration file [default: %default]",
                      default=os.path.join(basedir, "get_tweets.cfg"))
    parser.add_option("-o", "--out", dest="output_dir",
                      help="output directory [default: %default]",
                      default=os.path.join(basedir, "tweets"))
    parser.add_option("-v", "--verbose", dest="verbose",
                      help="verbose output [default: %default]",
                      action="store_true",
                      default=False)
    (options, args) = parser.parse_args()
    return options
    
    
if __name__ == "__main__":
    opts = parse_args()
    ts = TweetSweeper(opts.config_file, opts.output_dir, opts.verbose)
    ts.fetch_tweets()
    




