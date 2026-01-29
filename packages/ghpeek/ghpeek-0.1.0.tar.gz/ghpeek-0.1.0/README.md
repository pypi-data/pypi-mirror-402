# GHpeek - the easy Github repository viewer

![GHpeek screenshot](https://github.com/kimusan/ghpeek/blob/main/assets/screenshot.png)

GHpeek is a stylish python TUI to get an overview of your github repositories, pull requests, issues and more. You simply add the reposity to the list and GHpeek will then show you a clear and easy to read list of issues and pull requests. Unread items are highlighted so you can easily see what needs your attention.
The TUI will also show you a summary of the repository metrices like stars, forks, open issues and pull requests.

## Dependencies

- textual
- PyGithub
- rich
- markdown
- python-dotenv

## Installation

GHpeek can be installed via pip. Simply run the following command:

```bash
pip install ghpeek
```

or even btter with pipx:

```bash
pipx install ghpeek
```

## Usage

To start GHpeek, simply run the following command:

```bash
ghpeek
```

The TUI lets you add repositories by pressing `a`. If a GitHub token is configured, you can pick from your repositories, filter forks, personal, and private/public repos, or enter a repository name in the format `owner/repo`. Without a token, you can still enter repositories manually. 
The repo will get added to the list on the left. You can navigate through the list using the arrow keys and a quick view of the details like number of issues and pull requests, stars, forks, etc. is shown. Selecting a repository will show you the issues and pull requests in the main view. You can navigate through the issues and pull requests using the arrow keys. Pressing `Enter` opens a preview modal for the selected issue or pull request, and pressing `Enter` again opens it in your default web browser.
You can jump between issues and pull requests using the `i` and `p` keys or by pressing `tag` to go to next view area. Pressing `r` will refresh the data for the selected repository.
Press `c` to toggle showing closed issues and pull requests.
The UI is providing clear visual feedback when loading data or when an error occurs.

## GitHub token

To enable repository picking and increase API rate limits, set a personal access token in the `GITHUB_TOKEN` environment variable (recommended via a `.env` file in the project root). The token should include at least the `repo` scope if you want to access private repositories; public repositories work with no scopes or `public_repo`.

# License

The project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

# Contributing

I would love to see contributions to GHpeek! If you have any ideas for new features or improvements, please feel free to open an issue or submit a pull request.

# Acknowledgements

This project uses the following open source libraries:
 - [Textual]()
 - [PyGithub]()
 - [Rich]()
 - [markdown]()
 - [python-dotenv]()

GHpeek was inspired by other terminal-based tools and was originally written by [Kim Schulz](https://Schulz.dk).

# Roadmap

 - Add support for logging in with a Github token for private repositories
 - Add support for filtering issues and pull requests
 - Add reply to issues and pull requests directly from the TUI
