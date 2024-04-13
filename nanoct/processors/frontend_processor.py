from collections import defaultdict, OrderedDict
import json


def format_results(data, median_data):
    # Extend with min max avh and median duration
    for test in data:
        testcase_data = median_data.get(test['testcase'], {})
        median_duration = testcase_data.get('median_duration')
        for key, value in testcase_data.items():
            test[key] = value

        if median_duration is not None:
            # Calculate deviation if median duration exists
            test['deviation_from_median'] = test['duration'] - median_duration
        else:
            # Indicate absence of median data
            test['deviation_from_median'] = 'No median data available'
    return data


def format_frontend(data, count):
    grouped_data = defaultdict(list)

    pr_order = []  # To track the order of pull requests as they first appear
    for entry in data:
        pr = str(entry['pull_request'])
        if pr.isdigit():  # Check if pr is numeric
            if pr not in pr_order:
                pr_order.append(pr)
            grouped_data[pr].append(entry)

    # Process grouped data to create the desired structure, maintaining pull request order
    structured_data = OrderedDict()  # To maintain the order of insertion
    for pr in pr_order[:count]:
        entries = grouped_data[pr]
        # Find the first entry with a non-null values
        author = next((entry.get('author')
                      for entry in entries if entry.get('author')), '')
        avatar = next((entry.get('avatar')
                      for entry in entries if not "/.png" in entry.get('avatar')), '')
        revision = next((entry.get('revision')
                         for entry in entries if entry.get('revision')), '')
        branch = next((entry.get('branch')
                       for entry in entries if not "/None" in entry.get('branch')), '')
        pr_url = next((entry.get('pr_url')
                       for entry in entries if entry.get('pr_url')), '')
        title = next((entry.get('title')
                      for entry in entries if entry.get('type') != "commit"), '')

        header_data = {
            'pr_number': pr,
            'author': author,
            'avatar': avatar,
            'branch': branch,
            'pr_url': pr_url,
            'overall_status': entries[0]['overall_status'],
            'current_revision': revision,
            'last_modified': entries[0]['last_modified'],
            'merge_duration': entries[0]['duration_in_days'],
            'merged': entries[0].get('matching_commit'),
            'title': title,
        }

        structured_data[pr] = {
            'header': header_data,
            'entries': entries
        }
    return json.dumps(structured_data)
