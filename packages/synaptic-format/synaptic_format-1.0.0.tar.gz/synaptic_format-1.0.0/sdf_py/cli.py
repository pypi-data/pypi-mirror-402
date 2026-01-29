# sdf_py/cli.py
import json
import click
import numpy as np
from .reader import SDFReader

class NumpySafeEncoder(json.JSONEncoder):
    """A JSON encoder that can handle NumPy arrays by showing their metadata."""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return {
                "__tensor__": True,
                "dtype": str(obj.dtype),
                "shape": obj.shape
            }
        return json.JSONEncoder.default(self, obj)

@click.group()
def main():
    """Synaptic Data Format (SDF) command-line utility."""
    pass

@main.command()
@click.argument('filepath', type=click.Path(exists=True, dir_okay=False))
def inspect(filepath):
    """Inspect an SDF file and show its metadata and schema."""
    click.echo(f"Inspecting SDF file: {click.style(filepath, fg='cyan')}")
    try:
        with SDFReader(filepath) as reader:
            click.echo("\n--- File Header ---")
            click.echo(json.dumps(reader.header, indent=2))
            
            record_count = 0
            for _ in reader:
                record_count += 1
            
            click.echo("\n--- Summary ---")
            click.echo(f"Total Records: {click.style(str(record_count), fg='green')}")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'), err=True)

@main.command()
@click.argument('filepath', type=click.Path(exists=True, dir_okay=False))
@click.option('-n', '--num-records', default=5, help='Number of records to show.')
def head(filepath, num_records):
    """Show the first N records of an SDF file."""
    click.echo(f"Showing first {num_records} records from: {click.style(filepath, fg='cyan')}\n")
    try:
        with SDFReader(filepath) as reader:
            for i, (data, metadata) in enumerate(reader):
                if i >= num_records:
                    break
                click.echo(f"--- Record {i} ---")
                click.echo(click.style("Metadata:", bold=True))
                click.echo(json.dumps(metadata, indent=2))
                click.echo(click.style("Payload:", bold=True))
                click.echo(json.dumps(data, indent=2, cls=NumpySafeEncoder))
                click.echo()
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'), err=True)

if __name__ == '__main__':
    main()