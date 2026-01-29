import os
import hashlib
from typing import List, Dict, Any
from ecdsa import ellipticcurve, numbertheory
from ecdsa.curves import SECP256k1, NIST384p as SECP384r1

class ZKPEngine:
    """
    Motor ZKP completo con Bulletproofs para verificación criptográfica.
    Implementa range proofs con protocolo Bulletproofs, commitments Pedersen,
    verificación O(log n), soporte para curvas ECDSA, y serialización.
    """

    def __init__(self, curve=SECP256k1):
        self.curve = curve
        self.order = curve.order
        self.G = curve.generator
        # H = hash(G) para commitment Pedersen
        h_hash = hashlib.sha256((str(self.G.x()) + str(self.G.y())).encode()).digest()
        h_int = int.from_bytes(h_hash, 'big') % self.order
        if h_int == 0:
            h_int = 1
        self.H = self.G * h_int
        # B para blinding en Bulletproofs
        b_hash = hashlib.sha256(b'B').digest()
        b_int = int.from_bytes(b_hash, 'big') % self.order
        if b_int == 0:
            b_int = 1
        self.B = self.G * b_int

    def pedersen_commit(self, v: int, r: int) -> ellipticcurve.Point:
        """Genera un commitment Pedersen C = v*G + r*H"""
        return v * self.G + r * self.H

    def vector_commit(self, a: List[int], G_vec: List[ellipticcurve.Point],
                     b: List[int], H_vec: List[ellipticcurve.Point],
                     c: int, H_prime: ellipticcurve.Point) -> ellipticcurve.Point:
        """Commitment vectorial <a, G> + <b, H> + c*H'"""
        P = ellipticcurve.INFINITY  # Punto en el infinito
        for ai, Gi in zip(a, G_vec):
            if ai != 0:
                P += ai * Gi
        for bi, Hi in zip(b, H_vec):
            if bi != 0:
                P += bi * Hi
        if c != 0:
            P += c * H_prime
        return P

    def generate_range_proof(self, v: int, r: int, n: int = 64) -> Dict[str, Any]:
        """Genera una prueba Bulletproofs para range proof v ∈ [0, 2^n - 1]"""
        # Precomputar generadores
        g = int(hashlib.sha256(b'g').hexdigest(), 16) % self.order
        h = int(hashlib.sha256(b'h').hexdigest(), 16) % self.order
        G_vec = [self.G * pow(g, i+1, self.order) for i in range(n)]
        H_vec = [self.H * pow(h, i+1, self.order) for i in range(n)]

        # Descomposición binaria
        a_L = [(v >> i) & 1 for i in range(n)]
        a_R = [a - 1 for a in a_L]

        # Aleatorios alpha, rho
        alpha = int.from_bytes(os.urandom(32), 'big') % self.order
        rho = int.from_bytes(os.urandom(32), 'big') % self.order

        # A = <a_L, G> + <a_R, H> + alpha * B
        A = self.vector_commit(a_L, G_vec, a_R, H_vec, alpha, self.B)

        # Aleatorios s_L, s_R
        s_L = [int.from_bytes(os.urandom(32), 'big') % self.order for _ in range(n)]
        s_R = [int.from_bytes(os.urandom(32), 'big') % self.order for _ in range(n)]

        # S = <s_L, G> + <s_R, H> + rho * B
        S = self.vector_commit(s_L, G_vec, s_R, H_vec, rho, self.B)

        # Desafío y = H(A, S)
        y = int(hashlib.sha256((str(A.x()) + str(A.y()) + str(S.x()) + str(S.y())).encode()).hexdigest(), 16) % self.order

        # z = H(A, S, y)
        z = int(hashlib.sha256((str(A.x()) + str(A.y()) + str(S.x()) + str(S.y()) + str(y)).encode()).hexdigest(), 16) % self.order

        # l = a_L - z * 1^n + s_L * y
        l = [((a_L[i] - z) + s_L[i] * y) % self.order for i in range(n)]
        r = [((a_R[i] + z) + s_R[i] * y) % self.order for i in range(n)]

        # t(x) = <l(x), r(x)>
        l_prime = s_L
        r_prime = s_R
        t0 = sum(l[i] * r[i] for i in range(n)) % self.order
        t1 = (sum(l[i] * r_prime[i] for i in range(n)) + sum(l_prime[i] * r[i] for i in range(n))) % self.order
        t2 = sum(l_prime[i] * r_prime[i] for i in range(n)) % self.order

        # Aleatorios tau1, tau2
        tau1 = int.from_bytes(os.urandom(32), 'big') % self.order
        tau2 = int.from_bytes(os.urandom(32), 'big') % self.order

        # T1 = t1 * G + tau1 * H
        T1 = t1 * self.G + tau1 * self.H
        # T2 = t2 * G + tau2 * H
        T2 = t2 * self.G + tau2 * self.H

        # Desafío x = H(T1, T2)
        x = int(hashlib.sha256((str(T1.x()) + str(T1.y()) + str(T2.x()) + str(T2.y())).encode()).hexdigest(), 16) % self.order

        # taux = tau1 * x + tau2 * x^2 + z^2 * r
        taux = (tau1 * x + tau2 * pow(x, 2, self.order) + pow(z, 2, self.order) * r) % self.order
        # mu = alpha + rho * x
        mu = (alpha + rho * x) % self.order
        # t = t0 + t1 * x + t2 * x^2
        t = (t0 + t1 * x + t2 * pow(x, 2, self.order)) % self.order

        # Commitment C
        C = self.pedersen_commit(v, r)

        # P para inner product
        one_vec = [1] * n
        G_sum = self.vector_commit(one_vec, G_vec, [], [], 0, ellipticcurve.INFINITY)
        P = A + x * S + pow(z, 2, self.order) * C - z * G_sum - mu * self.H

        # Vectores para inner product
        a_vec = [(l[i] + x * l_prime[i]) % self.order for i in range(n)]
        b_vec = [(r[i] + x * r_prime[i]) % self.order for i in range(n)]
        H_prime = self.B

        # Generar prueba de producto interno
        inner_proof = self._generate_inner_product_proof(a_vec, b_vec, G_vec, H_vec, t, H_prime, P, n)

        return {
            'A': A, 'S': S, 'T1': T1, 'T2': T2,
            'taux': taux, 'mu': mu, 't': t,
            'inner_proof': inner_proof
        }

    def _generate_inner_product_proof(self, a: List[int], b: List[int],
                                     G_vec: List[ellipticcurve.Point], H_vec: List[ellipticcurve.Point],
                                     c: int, H_prime: ellipticcurve.Point, P: ellipticcurve.Point, n: int) -> Dict[str, Any]:
        """Genera prueba recursiva de producto interno <a, b> = c"""
        if n == 1:
            return {'a': a[0], 'b': b[0]}

        n_half = n // 2
        a_L, a_R = a[:n_half], a[n_half:]
        b_L, b_R = b[:n_half], b[n_half:]
        G_L, G_R = G_vec[:n_half], G_vec[n_half:]
        H_L, H_R = H_vec[:n_half], H_vec[n_half:]

        c_L = sum(a_L[i] * b_R[i] for i in range(n_half)) % self.order
        c_R = sum(a_R[i] * b_L[i] for i in range(n_half)) % self.order

        L = self.vector_commit(a_L, G_R, b_R, H_L, c_L, H_prime)
        R = self.vector_commit(a_R, G_L, b_L, H_R, c_R, H_prime)

        u = int(hashlib.sha256((str(L.x()) + str(L.y()) + str(R.x()) + str(R.y())).encode()).hexdigest(), 16) % self.order
        u_inv = numbertheory.inverse_mod(u, self.order)

        a_prime = [(a_L[i] * u + a_R[i] * u_inv) % self.order for i in range(n_half)]
        b_prime = [(b_L[i] * u_inv + b_R[i] * u) % self.order for i in range(n_half)]
        G_prime = [(G_L[i] * u_inv + G_R[i] * u) for i in range(n_half)]
        H_prime_new = [(H_L[i] * u + H_R[i] * u_inv) for i in range(n_half)]
        P_prime = L * pow(u, 2, self.order) + P + R * pow(u_inv, 2, self.order)

        proof = self._generate_inner_product_proof(a_prime, b_prime, G_prime, H_prime_new, c, H_prime, P_prime, n_half)
        proof.update({'L': L, 'R': R})
        return proof

    def verify_range_proof(self, C: ellipticcurve.Point, proof: Dict[str, Any], n: int = 64) -> bool:
        """Verifica una prueba Bulletproofs para range proof"""
        A, S, T1, T2 = proof['A'], proof['S'], proof['T1'], proof['T2']
        taux, mu, t = proof['taux'], proof['mu'], proof['t']
        inner_proof = proof['inner_proof']

        # Recalcular desafíos
        y = int(hashlib.sha256((str(A.x()) + str(A.y()) + str(S.x()) + str(S.y())).encode()).hexdigest(), 16) % self.order
        z = int(hashlib.sha256((str(A.x()) + str(A.y()) + str(S.x()) + str(S.y()) + str(y)).encode()).hexdigest(), 16) % self.order
        x = int(hashlib.sha256((str(T1.x()) + str(T1.y()) + str(T2.x()) + str(T2.y())).encode()).hexdigest(), 16) % self.order

        # Precomputar generadores
        g = int(hashlib.sha256(b'g').hexdigest(), 16) % self.order
        if g == 0:
            g = 1
        h = int(hashlib.sha256(b'h').hexdigest(), 16) % self.order
        if h == 0:
            h = 1
        G_vec = [self.G * pow(g, i+1, self.order) for i in range(n)]
        H_vec = [self.H * pow(h, i+1, self.order) for i in range(n)]

        # Calcular P
        one_vec = [1] * n
        G_sum = self.vector_commit(one_vec, G_vec, [], [], 0, ellipticcurve.Point(self.curve.curve, 0, 0))
        P = A + x * S + pow(z, 2, self.order) * C - z * G_sum - mu * self.H

        # Verificar inner product
        H_prime = self.B
        return self._verify_inner_product_proof(inner_proof, P, G_vec, H_vec, t, H_prime, n)

    def _verify_inner_product_proof(self, proof: Dict[str, Any], P: ellipticcurve.Point,
                                   G_vec: List[ellipticcurve.Point], H_vec: List[ellipticcurve.Point],
                                   c: int, H_prime: ellipticcurve.Point, n: int) -> bool:
        """Verifica prueba recursiva de producto interno"""
        if n == 1:
            a, b = proof['a'], proof['b']
            expected_P = a * G_vec[0] + b * H_vec[0] + c * H_prime
            return P == expected_P

        L, R = proof['L'], proof['R']
        u = int(hashlib.sha256((str(L.x()) + str(L.y()) + str(R.x()) + str(R.y())).encode()).hexdigest(), 16) % self.order
        u_inv = numbertheory.inverse_mod(u, self.order)

        n_half = n // 2
        G_L, G_R = G_vec[:n_half], G_vec[n_half:]
        H_L, H_R = H_vec[:n_half], H_vec[n_half:]
        G_prime = [(G_L[i] * u_inv + G_R[i] * u) for i in range(n_half)]
        H_prime_new = [(H_L[i] * u + H_R[i] * u_inv) for i in range(n_half)]
        P_prime = L * pow(u, 2, self.order) + P + R * pow(u_inv, 2, self.order)

        return self._verify_inner_product_proof(proof, P_prime, G_prime, H_prime_new, c, H_prime, n_half)

    def generate_proof(self, value: int, randomness: int, n: int = 64) -> Dict[str, Any]:
        """Método principal para generar prueba"""
        return self.generate_range_proof(value, randomness, n)

    def verify_proof(self, commitment: ellipticcurve.Point, proof: Dict[str, Any], n: int = 64) -> bool:
        """Método principal para verificar prueba"""
        return self.verify_range_proof(commitment, proof, n)

    def serialize_proof(self, proof: Dict[str, Any]) -> bytes:
        """Serializa la prueba a bytes"""
        import pickle
        return pickle.dumps(proof)

    def deserialize_proof(self, data: bytes) -> Dict[str, Any]:
        """Deserializa la prueba desde bytes"""
        import pickle
        return pickle.loads(data)

# Funciones de conveniencia

def create_zkp_engine(curve=SECP256k1) -> ZKPEngine:
    """Crear instancia del motor ZKP."""
    return ZKPEngine(curve)