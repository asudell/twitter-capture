#! /usr/bin/env python

import sys, os

class TweetSweeper:
    def __init__(self, config_file, output_dir, verbose=False):
        self.config_file = config_file
        self.output_dir = output_dir
        self.verbose = verbose

    def parse_config(self):
        import ConfigParser
        config = ConfigParser.ConfigParser()
        config.read(self.config_file)
        self.token = config.get('auth', 'token')
        self.token_key = config.get('auth', 'token_key')
        self.secret = config.get('auth', 'secret')
        self.secret_key = config.get('auth', 'secret_key')
        self.terms = list()
        for t in config.items('terms'):
            self.terms.append(t[1])

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
        for query in self.terms:
            tweets = t.search.tweets(q=query, result_type='recent', count=100)

            import simplejson as json
            import codecs
            for tweet in tweets['statuses']:
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
    




