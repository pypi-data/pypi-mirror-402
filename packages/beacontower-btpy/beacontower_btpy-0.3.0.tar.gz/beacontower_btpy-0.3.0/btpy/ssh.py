# Import the certificate classes
import typer
from sshkey_tools.keys import (
    EcdsaCurves,
    EcdsaPrivateKey,
    Ed25519PrivateKey,
    PrivateKey,
    RsaPrivateKey,
)

app = typer.Typer()


@app.command()
def keypair(
    key_type: str = typer.Option("rsa", help="The type of key to generate"),
    key_size: int = typer.Option(2048, help="The size of the key to generate"),
    output_file: str = typer.Option("id_rsa", help="The file to save the key to"),
    password: str = typer.Option("", help="The password to encrypt the key with"),
):
    """
    Generate a new keypair
    """
    if key_type == "rsa":
        rsa_priv = RsaPrivateKey.generate(key_size)
        rsa_priv.to_file(output_file, password)
    elif key_type == "ecdsa":
        ecdsa_priv = EcdsaPrivateKey.generate(EcdsaCurves.NISTP256)
        ecdsa_priv.to_file(output_file, password)
    elif key_type == "ed25519":
        ed25519_priv = Ed25519PrivateKey.generate()
        ed25519_priv.to_file(output_file, password)


@app.command()
def public_key(
    key_type: str = typer.Option("rsa", help="The type of key to generate"),
    input_file: str = typer.Option("id_rsa", help="The file to read the key from"),
    output_file: str = typer.Option("id_rsa.pub", help="The file to save the key to"),
):
    """
    Generate a public key from a private key
    """
    priv = PrivateKey.from_file(input_file)
    pub = priv.public_key()
    pub.to_file(output_file)


@app.command()
def download_keypair():
    """
    Download a keypair from a remote server
    """
    pass


if __name__ == "__main__":
    app()
