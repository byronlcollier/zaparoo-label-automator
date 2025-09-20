from wrapper.twitch import TokenManager

def main():
    twitch_token = TokenManager(config_path="./.config")
    twitch_token.initialise_token()
    print(twitch_token.token)


if __name__ == "__main__":
    main()
