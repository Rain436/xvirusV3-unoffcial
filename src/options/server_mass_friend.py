
import datetime
import time
from concurrent.futures import ThreadPoolExecutor

from colorama import Fore

from src import *

def server_mass_friend():
    Output.SetTitle(f"Server Mass Friend")
    sent = 0
    error = 0
    args = []
    tokens = TokenManager.get_tokens()
    id_scraper()
    user_scraper()

    def runFrinder(token, username):
        proxy = "http://" + ProxyManager.clean_proxy(ProxyManager.random_proxy())
        retry, rqdata, rqtoken = send(token, username, "","")
        if retry:
            solver = Captcha(proxy=proxy, siteKey="b2b02ab5-7dae-4d6f-830e-7b55634c888b", siteUrl="https://discord.com/", rqdata=rqdata)
            Output("cap", config).log(f'Solving Captcha...')
            capkey = solver.solveCaptcha()
            if capkey is not None:
                Output("cap", config).log(f"Solved -> {Fore.LIGHTBLACK_EX} {capkey[-40:]}")
            else: 
                Output("bad", config).log(f"Failed To Solve -> {Fore.LIGHTBLACK_EX} {capkey}")
            send(token, username, capkey, rqtoken)

    def send(token, username, capkey, rqtoken):
        nonlocal sent, error
        session, headers, cookie = Header.get_client(token)
        
        if capkey != "":
            headers["x-captcha-key"] = capkey
            headers["x-captcha-rqtoken"] = rqtoken
            
        result = session.post(f"https://discord.com/api/v9/users/@me/relationships", headers=headers, cookies=cookie, json={
            'session_id': utility.rand_str(32),
            'username': username,
        })

        if result.status_code == 204:
            Output("good", config, token).log(f"Success -> {token} {Fore.LIGHTBLACK_EX}({result.status_code})")
            sent += 1
            return False, None, None  
        elif result.text.startswith('{"captcha_key"'):
            Output("bad", config, token).log(f"Error -> {token} {Fore.LIGHTBLACK_EX}({result.status_code}) {Fore.RED}(Captcha)")
            use_captcha = config._get("use_captcha")
            if use_captcha is True:
                return True, result.json()["captcha_rqdata"], result.json()["captcha_rqtoken"]
            else:
                return False, None, None 
                error += 1
        elif result.text.startswith('{"message": "401: Unauthorized'):
            Output("bad", config, token).log(f"Error -> {token} {Fore.LIGHTBLACK_EX}({result.status_code}) {Fore.RED}(Unauthorized)")
            error += 1
            return False, None, None  
        elif "Cloudflare" in result.text:
            Output("bad", config, token).log(f"Error -> {token} {Fore.LIGHTBLACK_EX}({result.status_code}) {Fore.RED}(CloudFlare Blocked)")
            error += 1
            return False, None, None  
        elif "\"code\": 40007" in result.text:
            Output("bad", config, token).log(f"Error -> {token} {Fore.LIGHTBLACK_EX}({result.status_code}) {Fore.RED}(Token Banned)")
            error += 1
            return False, None, None  
        elif "\"code\": 40002" in result.text:
            Output("bad", config, token).log(f"Error -> {token} {Fore.LIGHTBLACK_EX}({result.status_code}) {Fore.RED}(Locked Token)")
            error += 1
            return False, None, None  
        elif "\"code\": 10006" in result.text:
            Output("bad", config, token).log(f"Error -> {token} {Fore.LIGHTBLACK_EX}({result.status_code}) {Fore.RED}(Invalid Invite)")
            error += 1
            return False, None, None  
        else:
            Output("bad", config, token).log(f"Error -> {token[:40]} {Fore.LIGHTBLACK_EX}({result.status_code}) {Fore.RED}({result.text})")
            error += 1

        return False
    def thread_complete(future):
        nonlocal sent, error
        result = future.result()

    if tokens is None:
        Output("bad", config).log("Token retrieval failed or returned None.")
        Output.PETC()
        return

    usernames  = utility.get_usernames()
    username = random.choice(usernames)
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
                    args = [token, username]
                    future = executor.submit(runFrinder, *args)
                    future.add_done_callback(thread_complete)
                    time.sleep(0.1)
                except Exception as e:
                    Output("bad", config).log(f"{e}")

        elapsed_time = time.time() - start_time
        Output("info", config).notime(f"Sent Friend Request Using {str(sent)} Tokens In {elapsed_time:.2f} Seconds")

        info = [
            f"{Fore.LIGHTGREEN_EX}Sent: {str(sent)}",
            f"{Fore.LIGHTRED_EX}Errors: {str(error)}",
            f"{Fore.LIGHTCYAN_EX}Total: {len(tokens)}"
        ]

        status = f"{Fore.RED} | ".join(info) + f"{Fore.RED}"
        print(f" {status}")
        Captcha.getCapBal()
        print()
        Output.PETC()
    else:
        Output("bad", config).log(f"No tokens were found in cache")
        Output.PETC()