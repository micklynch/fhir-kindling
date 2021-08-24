"""Console script for fhir_kindling."""
import os
import sys
import click
import yaml
from fhir_kindling.generators import PatientGenerator
from fhir_kindling.bundle import upload_bundle
from pathlib import Path
from dotenv import load_dotenv,find_dotenv


@click.group()
def main():
    """Command line interface for generating synthetic FHIR resources and uploading them to a FHIR server."""
    load_dotenv(find_dotenv())


@main.command()
@click.option("-f", "--file", default=None, help="Path to a .yml file defining the generation specs.")
@click.option("-n", "--n-patients", default=None, help="How many patients to generate", type=int)
@click.option("-a", "--age-range", default=None, help="Space separated min/max age of patients.",
              type=click.Tuple([int, int]))
@click.option("-o", "--output", default=None, help="Path where the generated resource bundle should be stored.")
@click.option("--upload", is_flag=True)
@click.option("--url", default=None, help="url of the FHIR api endpoint to upload the bundle to.")
@click.option("--username", default=None, help="username for basic auth")
@click.option("--password", default=None, help="password for basic auth")
@click.option("--token", default=None, help="token for bearer token auth")
def generate(file, n_patients, age_range, output, url, upload, username, password, token):
    """Generate FHIR resource bundles"""
    if file:
        click.echo(f"Generating FHIR resources defined in:\n{file}")
        with open(file, "r") as f:
            resource_specs = yaml.safe_load(f)
            click.echo(resource_specs)
    else:
        if not n_patients:
            n_patients = click.prompt("Enter the number of patients you want to create", default=100)

        # Prompt for age range if not given
        if not age_range:
            min_age = click.prompt("Enter the min age patients", default=18, type=int)
            max_age = click.prompt("Enter the max age patients", default=101, type=int)
            age_range = (min_age, max_age)

        # Generate the patients
        patient_generator = PatientGenerator(n_patients, age_range=age_range)
        patients = patient_generator.generate()

        # TODO if FHIR server is given upload the resources to get server generated ids
        if click.confirm("Generate additional resources for patients?"):
            patient_resource = click.prompt("Select resource:", type=click.Choice(["Observation", "Condition"]))
        else:
            pass

    if upload:
        if not url:
            click.prompt("Enter your FHIR server`s API url")

    if not output:
        if click.confirm("No storage location given. Exit without saving generated resources?"):
            return 0
        else:
            output = click.prompt("Enter the path or filename under which the bundle should be stored",
                                       default="bundle.json")
            if Path(output).exists():
                overwrite = click.confirm(f"File already exists. Overwrite {output}?")
                if not overwrite:
                    output = click.prompt("Enter new filepath")
            with open(output, "w") as output_file:
                bundle = patient_generator.make_bundle()
                output_file.write(bundle.json(indent=2))
    click.echo(f"Storing resources in {output}")

    return 0


@main.command()
@click.argument("bundle")
@click.option("--url", help="url of the FHIR api endpoint to upload the bundle to.")
@click.option("-u", "--username", default=None, help="Password to get when authenticating against basic auth.")
@click.option("-p", "--password", default=None, help="Username to use when authenticating with basic auth.")
@click.option("--token", default=None, help="Token to use with bearer token auth.")
def upload(bundle, url, username, password, token):
    """Upload a bundle to a fhir server"""

    # Get the url

    if not username or password or token:
        click.confirm("Attempt upload without adding authentication?")
    upload_bundle(bundle, fhir_api_url=url, username=username, password=password, token=token)

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
