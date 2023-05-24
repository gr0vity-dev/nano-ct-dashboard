class GithubUrlBuilder:

    @staticmethod
    def get_report_url(hash, testcase):
        return f"https://raw.githubusercontent.com/gr0vity-dev/nano-node-builder/main/continuous_testing/{hash}_{testcase}.txt"

    @staticmethod
    def create_gh_url(data):
        if "type" not in data:
            return None
        base_url = "https://github.com/nanocurrency/nano-node"
        if data['type'] == 'pull_request':
            # If it's a pull request, link to the pull request
            return f"{base_url}/pull/{data['pull_request']}"
        else:
            # If it's a commit, link to the commit
            return f"{base_url}/commit/{data['hash']}"
