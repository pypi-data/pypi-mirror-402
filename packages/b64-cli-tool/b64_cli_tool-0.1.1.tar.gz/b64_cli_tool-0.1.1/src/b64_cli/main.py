import base64
import binascii

import click


@click.command(name="b64")
@click.option(
    "-d",
    "--decode",
    "decode_value",
    help="Base64 string to decode.",
)
@click.option(
    "-e",
    "--encode",
    "encode_value",
    help="String to encode as base64.",
)
def b64(decode_value: str | None, encode_value: str | None) -> None:
    if bool(decode_value) == bool(encode_value):
        raise click.ClickException("Use exactly one of --decode/-d or --encode/-e.")

    if decode_value:
        try:
            decoded_bytes = base64.b64decode(decode_value, validate=True)
            decoded_text = decoded_bytes.decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise click.ClickException(f"Invalid base64 input: {exc}") from exc

        click.echo(decoded_text)
        return

    if encode_value:
        encoded_bytes = encode_value.encode("utf-8")
        encoded_text = base64.b64encode(encoded_bytes).decode("ascii")
        click.echo(encoded_text)


if __name__ == "__main__":
    b64()
