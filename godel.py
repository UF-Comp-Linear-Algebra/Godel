import csv
from typing import List

import click

from scantron import Key, Scantron, Grader


@click.group()
def cli():
    pass

# TODO name argument
@cli.command()
@click.argument('file', type=click.File('r'), required=True)
# output file is optional and defaults to stdout if not provided. can be provided with -o flag or --output flag and will overwrite the file if it already exists
@click.option('-o', '--output', 'output', type=click.File('w'), default=None)
def grade(file, output):
    """Grade a scantron file."""
    # read csv file
    reader = csv.reader(file)

    # separate keys and scantrons
    keys: List[Key] = []
    scantrons: List[Scantron] = []
    for row in reader:
        if row[1] == 'KEY' and row[2] == '':
            keys.append(Key.parse(row))
        else:
            scantrons.append(Scantron.parse(row))

    # grade scantrons
    grades = Grader(keys).grade_all(scantrons)

    if output is None:
        for grade in grades:
            click.echo(grade)
    else:
        writer = csv.writer(output)
        # iterate and unpack grades into name, id, and score
        for grade in grades:
            writer.writerow([
                grade.student.name,
                grade.student.sid,
                'INVALID INFO' if not grade.student.is_valid else '',
                grade.points,
                grade.out_of,
                round(100 * grade.points / grade.out_of, 2),
                grade.form.value
            ])


if __name__ == '__main__':
    cli()
