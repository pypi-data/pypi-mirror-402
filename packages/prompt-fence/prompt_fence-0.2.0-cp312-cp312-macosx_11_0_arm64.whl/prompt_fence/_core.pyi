class FenceError(Exception):
    """Raised when a fence validation fails or structure is invalid."""

class CryptoError(Exception):
    """Raised when cryptographic operations (signing/verifying) fail."""

class FenceType:
    INSTRUCTIONS: str
    CONTENT: str
    DATA: str

class FenceRating:
    TRUSTED: str
    UNTRUSTED: str
    PARTIALLY_TRUSTED: str

def generate_keypair() -> tuple[str, str]: ...
def verify_all_fences(prompt: str, public_key: str) -> bool: ...
def verify_fence(fence_xml: str, public_key: str) -> tuple[bool, str, str, str, str, str]: ...
def get_awareness_instructions() -> str: ...
def set_awareness_instructions(instructions: str) -> None: ...
