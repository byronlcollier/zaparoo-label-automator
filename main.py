# from wrapper.twitch import TokenManager
from wrapper.igdb import IGDBWrapper

def main():
    # twitch_token = TokenManager(config_path="./.config")
    # twitch_token.initialise_token()
    # print(twitch_token.value)

    api = IGDBWrapper(config_path="./.config")

    print(api.token)


if __name__ == "__main__":
    main()
