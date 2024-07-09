import os
import asyncio
import httpx
import logging
from colorama import Fore, init
from itertools import cycle
from tqdm import tqdm

# initilizing colorama
init(autoreset=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Clear console
os.system("cls" if os.name == "nt" else "clear")

# Read tokens and proxies
def read_file_lines(filename):
    with open(filename, "r") as file:
        return file.read().splitlines()

tokens = set(read_file_lines("tokens.txt"))  
proxies = cycle(read_file_lines("proxies.txt"))

logo = """
                  __                    __      __ 
_______   ____  _/  |_ _______   ____  /  \    /  \
\_  __ \_/ __ \ \   __\\_  __ \ /  _ \ \   \/\/   /
 |  | \/\  ___/  |  |   |  | \/(  <_> ) \        / 
 |__|    \___  > |__|   |__|    \____/   \__/\  /  
             \/                               \/   
"""


print(logo)

# Function for deleting channel
async def delete_channel(sem, client, token, channel_id, headers, retries=3):
    for attempt in range(retries):
        try:
            async with sem:
                response = await client.delete(f"https://discordapp.com/api/v9/channels/{channel_id}?silent=false", headers=headers)
                response.raise_for_status()  # Raise HTTP errors if any
                logging.info(f"NukingChannel: {channel_id} deleted")
                return True
        except httpx.HTTPStatusError as http_err:
            if http_err.response.status_code == 429:
                retry_after = int(http_err.response.headers.get("Retry-After", 5)) + 1
                logging.warning(f"NukingChannel: | Rate limited on channel: {channel_id}. Retrying after {retry_after} seconds...")
                await asyncio.sleep(retry_after)
            else:
                logging.error(f"NukingChannel: {channel_id} | HTTP Error: {http_err.response.status_code} - {http_err.response.text}")
                return False
        except httpx.RequestError as req_err:
            logging.error(f"NukingChannel: {channel_id} | Request Error: {req_err}")
            return False
    return False

# Cleaner function
async def cleaner(token):
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        sem = asyncio.Semaphore(10)  # Limit concurrency to 10 requests
        channels_deleted = 0
        try:
            while True:
                response = await client.get("https://discordapp.com/api/v9/users/@me/channels", headers=headers)
                channels = response.json()

                if not channels:
                    break

                tasks = []
                for channel in channels:
                    tasks.append(delete_channel(sem, client, token, channel['id'], headers))

                results = await asyncio.gather(*tasks)
                
                # Counts deleted channels
                channels_deleted += sum(results)

                # Remove token if all channels successfully purged
                if all(results):
                    tokens.remove(token)

        except httpx.HTTPStatusError as http_err:
            if http_err.response.status_code == 429:
                logging.warning(f"NukingChannel: | Rate limited globally. Retrying after {retry_after} seconds...")
                retry_after = int(http_err.response.headers.get("Retry-After", 5)) + 1
                await asyncio.sleep(retry_after)
            else:
                logging.error(f"NukingChannel: | HTTP Error: {http_err.response.status_code} - {http_err.response.text}")
        except httpx.RequestError as req_err:
            logging.error(f"NukingChannel: | Request Error: {req_err}")
        except Exception as e:
            logging.error(f"NukingChannel: | Error: {str(e)}")
        finally:
            logging.info(f"NukingChannel: | Total Channels Deleted: {channels_deleted}")

# Main function for cleaner tasks
async def main():
    tasks = [cleaner(token) for token in tokens]
    with tqdm(total=len(tokens), desc="Overall Progress") as pbar:
        for task in asyncio.as_completed(tasks):
            await task
            pbar.update(1)

# Entry point
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Process interrupted by user.")
    finally:
        print(Fore.GREEN + "Done nigger")

# 8tpz on cord