import click
import json
import requests
from bs4 import BeautifulSoup


@click.command()
def main():
    """GCP IAM DataSet
    """
    response = requests.get(
        'https://cloud.google.com/iam/docs/custom-roles-permissions-support')
    soup = BeautifulSoup(response.text, 'html.parser')
    perms = []
    for idx, row in enumerate(soup.select_one('#table-div-id').select('tr')):
        if not idx:
            continue
        perms.append(row.td.code.text)

    with open('gcp-iam-perms.json', 'w') as fh:
        json.dump({'permissions': perms}, fp=fh, indent=2)


if __name__ == '__main__':
    main()
