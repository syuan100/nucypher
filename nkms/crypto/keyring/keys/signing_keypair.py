import msgpack
from random import SystemRandom
from py_ecc.secp256k1 import N, privtopub, ecdsa_raw_sign, ecdsa_raw_recover


class SigningKeypair(object):
    def __init__(self, privkey_bytes=None):
        self.secure_rand = SystemRandom()
        if privkey_bytes:
            self.priv_key = privkey_bytes
        else:
            # Key generation is random([1, N - 1])
            priv_number = self.secure_rand.randrange(1, N)
            self.priv_key = priv_number.to_bytes(32, byteorder='big')
        # Get the public component
        self.pub_key = privtopub(self.priv_key)

    def _vrs_msgpack_dump(self, v, r, s):
        v_bytes = v.to_bytes(1, byteorder='big')
        r_bytes = r.to_bytes(32, byteorder='big')
        s_bytes = s.to_bytes(32, byteorder='big')
        return msgpack.dumps((v_bytes, r_bytes, s_bytes))

    def _vrs_msgpack_load(self, msgpack_vrs):
        sig = msgpack.loads(msgpack_vrs)
        v = int.from_bytes(sig[0], byteorder='big')
        r = int.from_bytes(sig[1], byteorder='big')
        s = int.from_bytes(sig[2], byteorder='big')
        return (v, r, s)


    def sign(self, msghash):
        """
        Signs a hashed message and returns a msgpack'ed v, r, and s.

        :param bytes msghash: Hash of the message

        :rtype: Bytestring
        :return: Msgpacked bytestring of v, r, and s (the signature)
        """
        v, r, s = ecdsa_raw_sign(msghash, self.priv_key)
        return self._vrs_msgpack_dump(v, r, s)

    def verify(self, msghash, signature):
        """
        Takes a msgpacked signature and verifies the message.

        :param bytes msghash: The hashed message to verify
        :param bytes signature: The msgpacked signature (v, r, and s)

        :rtype: Boolean
        :return: Is the signature valid or not?
        """
        sig = self._vrs_msgpack_load(signature)
        # Generate the public key from the signature and validate
        # TODO: Look into fixed processing time functions for comparison
        verify_sig = ecdsa_raw_recover(msghash, sig)
        return verify_sig == self.pub_key
