# 
# install python3.10
# pip install twscrape python-telegram-bot
# twscrape add_accounts login.txt username
# twscrape login_accounts --manual # user login
# twscrape user_by_login <user_name> # query user info
# twscrape accounts  # query login user

import asyncio
import twscrape

async def worker(api: twscrape.API, uid: str):
    tweets = []
    try:
        tss = await twscrape.gather(api.user_tweets(uid, limit=10))
        for i in tss:
            tw = {"id": i.id_str, "datetime": i.date.strftime('%Y-%m-%d %H:%M:%S'),
                "url": i.url, "rawContent": i.rawContent, "media": i.media.dict()}
            tweets.append(tw)
            print(tw)
        tweets.sort(key=lambda x: x['datetime'], reverse=True)
    except Exception as e:
        print(e)
    finally:
        return tweets


async def main():
    api = twscrape.API()
    user_id = 'xxxxxx' # first get user_id
    results = await asyncio.gather(worker(api, user_id))
    print()
    print()
    for i in results[0]:
        print(i)

if __name__ == "__main__":
    asyncio.run(main())
