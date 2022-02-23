from searchtweets import load_credentials, gen_request_parameters, ResultStream
from os import system

import pandas as pd
import pyfiglet
import spacy

class MathAlacarte(object):
    def __init__(self, query: str):
        self.query = query
        self.search_args = self.authenticate()
        self.nlp = spacy.load('en_core_web_lg')
        self.tweets = self.search()
        self.tweets_df = self.get_tweets_df()


    def __repr__(self):
        return f'\nFound {len(self.tweets_df)} tweets:\n\n{self.tweets_df.tweet_text}\n'


    def authenticate(self) -> dict:
        creds = load_credentials(filename='.twitter_keys.yaml',
                                 yaml_key='search_tweets_v2',
                                 env_overwrite=False)

        return creds

    def search(self) -> list[dict]:
        params = gen_request_parameters(query=self.query, 
                                        results_per_call=100,
                                        granularity=None, 
                                        tweet_fields='author_id',
                                        user_fields='username',
                                        expansions='author_id')

        rs = ResultStream(request_parameters=params,
                        max_results=1000,
                        max_pages=1,
                        **self.search_args)

        tweets = list(rs.stream())

        return tweets


    def get_tweets_df(self) -> pd.DataFrame:
        users = {}

        for i in self.tweets:
            for u in i['includes']['users']:
                id = u['id']
                username = u['username']

                if id not in users:
                    users[id] = username

        results = {}
        docs = set()

        for i in self.tweets:
            for j in i['data']:
                _ = j['text'].lower().replace('\n\n', ' ').replace('\n', ' ')

                if len(_) <= 300:
                    doc = self.nlp(_)
                    plural = ['us', 'we', 'our']

                    if any([i in doc.text for i in plural]):
                        continue

                    else: 
                        user = users[j['author_id']]

                        if not docs:
                            results[user] = [doc.text, j['id']]

                        else: 
                            similar = [d.similarity(doc) for d in docs]

                            if all([j <= .99 for j in similar]):
                                if user not in results:
                                    results[user] = [doc.text, j['id']]

                                else: 
                                    results[user].append([doc.text, j['id']])

                    docs.add(doc)

        df = pd.DataFrame(data=results.items(), columns=['username', 'data'])
        df['tweet_id'] = df['data'].apply(lambda x: x[1])
        df['tweet_text'] = df['data'].apply(lambda x: x[0])
        df.drop(columns=['data'], inplace=True)

        return df

    def load_targets(self, targets: list[int]) -> str:
        s = ''

        for i in targets:
            _id = self.tweets_df.iloc[i].id
            _user = self.tweets_df.iloc[i].username

            s += f"https://twitter.com/{_user}/status/{_id} "

        return s

if __name__ == '__main__':
    system('clear')
    print(pyfiglet.figlet_format("tutor reesh", font="cybermedium"))

    query = input('Enter search query: ')

    if query == 'reesh':
        query = """(("take my" OR "do my" OR "good money" OR "give you" OR "pay someone" OR "pay you") (test OR exam OR assignment OR midterm OR final OR class OR course) (math OR calc OR calculus OR precalc OR stats OR statistics OR stat OR chemistry OR chem OR biology OR bio OR physics OR phys OR phy)) lang:en -is:retweet -has:media -has:links -has:mentions -is:quote -has:hashtags"""

    m = MathAlacarte(query=query)

    print(m,'\n')

    while True:
        choice1 = input('Continue? (y/n): ')

        if choice1 == 'y':
            while True:
                targets = input('\nEnter tweet indices to load, separated by a comma: ')
                targets = [int(i) for i in targets.replace(' ', '').split(',')]

                if isinstance(targets, list) and all([isinstance(i, int) for i in targets]):

                    try:
                        urls = m.load_targets(targets)
                        print(f'\nurls: {urls}\n')

                    except ValueError:
                        print('Welp, something broke. One more try? (y/n): ')

                        if input() == 'y':
                            continue

                        else:
                            print('Okay... BYE!')
                            break

                    choice2 = input('Open in browser? (y/n): ')

                    if choice2 == 'y':
                        system(f'open {urls}')
                        exit()

                    else: exit()

                else:
                    choice3 = input('\nInvalid input. Try again? (y/n): \n')

                    if choice3 == 'y':
                        continue

                    else: exit()

        else:
            print('Okay... BYE!')
            exit()