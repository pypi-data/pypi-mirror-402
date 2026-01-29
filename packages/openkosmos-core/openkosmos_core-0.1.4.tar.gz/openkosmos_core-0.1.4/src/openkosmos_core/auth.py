import time
from typing import Optional

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from openkosmos_core.common.model import BaseConfig


class AuthTokenConfig(BaseConfig):
    private_key: Optional[str]
    public_key: Optional[str]
    algorithms: Optional[str] = "RS256"


class AuthToken:
    """
    auth token, use following command to generate key pair

    openssl genrsa -out private_key.pem 2048
    openssl rsa -in private_key.pem -pubout -out public_key.pem

    or use

    generate_rsa_keypair()

    """

    def __init__(self, config: AuthTokenConfig):
        self._config = config
        self._init(private_key=config.private_key,
                   public_key=config.public_key,
                   algorithms=config.algorithms)

    def config(self) -> AuthTokenConfig:
        return self._config

    def _init(self, private_key: str = None, public_key: str = None, algorithms: str = "RS256"):
        if algorithms == "RS256" or algorithms == "PS256":
            self.private_key = private_key.strip()
            self.public_key = public_key.strip()
        else:
            self.private_key = private_key.strip()

        self.algorithms = algorithms

    def generate(self, data: dict, expired_seconds: int = 300) -> str:
        payload = data
        payload["exp"] = int(time.time()) + expired_seconds
        return jwt.encode(payload, self.private_key, algorithm=self.algorithms);

    def retrieve(self, token: str, verify_signature=True, algorithms=None):
        actual_algorithms = self.algorithms if algorithms is None else algorithms
        if verify_signature:
            if self.public_key is None:
                payload = jwt.decode(token.strip(), self.private_key, algorithms=actual_algorithms)
            else:
                payload = jwt.decode(token.strip(), self.public_key, algorithms=actual_algorithms)
        else:
            payload = jwt.decode(token.strip(), options={"verify_signature": False},
                                 algorithms=actual_algorithms)
        del payload["exp"]
        return payload

    def generate_auth_headers(self, data: dict, expired_seconds: int = 300) -> str:
        payload = data
        payload["exp"] = int(time.time()) + expired_seconds

        gateway_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.generate(data, expired_seconds)}"
        }

        return gateway_headers;

    @staticmethod
    def generate_rsa_config(key_size: int = 2048):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key = private_key.public_key()

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return AuthTokenConfig(private_key=private_pem.decode(),
                               public_key=public_pem.decode())
