
import datetime
import time
from concurrent.futures import ThreadPoolExecutor

from colorama import Fore

from src import *

def bypass_rules():
    Output.set_title(f"Rules Bypasser")
    accepted = 0
    error = 0
    args = []
    tokens = TokenManager.get_tokens()

    def accept(token, guild_id):
        nonlocal accepted, error
        session = Client.get_session(token)
        rules = session.get(f"https://discord.com/api/v9/guilds/{guild_id}/member-verification?with_guild=false").json()
        result = session.put(f"https://discord.com/api/v9/guilds/{guild_id}/requests/@me", json=rules)

        if result.status_code == 201:
            Output("good", config, token).log(f"Success -> {token} {Fore.LIGHTBLACK_EX}({result.status_code})")
            accepted += 1
        else:
            Output.error_logger(token, result.text, result.status_code)
            error += 1

    def thread_complete(future):
        nonlocal accepted, error
        debug = config._get("debug_mode")
        try:
            result = future.result()
        except Exception as e:
            if debug:
                if "failed to do request" in str(e):
                    message = f"Proxy Error -> {str(e)[:80]}..."
                else:
                    message = f"Error -> {e}"
                Output("dbg").log(message)
            else:
                pass

    if tokens is None:
        Output("bad").log("Token retrieval failed or returned None.")
        Output.PETC()
        return

    guild_id = utility.ask("Guild ID")
    max_threads = utility.asknum("Thread Count")

    try:
        if not max_threads.strip():
            max_threads = "16"
        else:
            max_threads = int(max_threads)
    except ValueError:
        max_threads = "16"

    if tokens:
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            for token in tokens:
                try:
                    token = TokenManager.OnlyToken(token)
                    args = [token, guild_id]
                    future = executor.submit(accept, *args)
                    future.add_done_callback(thread_complete)
                    time.sleep(0.1)
                except Exception as e:
                    Output("bad").log(f"{e}")

        elapsed_time = time.time() - start_time
        Output("info").notime(f"{str(accepted)} Tokens Accepted Rules In {elapsed_time:.2f} Seconds")

        info = [
            f"{Fore.LIGHTGREEN_EX}Accepted: {str(accepted)}",
            f"{Fore.LIGHTRED_EX}Errors: {str(error)}",
            f"{Fore.LIGHTCYAN_EX}Total: {len(tokens)}"
        ]

        status = f"{Fore.RED} | ".join(info) + f"{Fore.RED}\n"
        print(f" {status}")
        Output.PETC()
    else:
        Output("bad").log(f"No tokens were found in cache")
        Output.PETC()