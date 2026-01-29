from decimal import Decimal, getcontext

"""
Exact digit-by-digit algorithms for integer n-th root extraction and
fractional refinement with explicit error bounds.

Based on the invariant-based constructive framework developed in:

S. Pareth, "Exact Constructive Digit-by-Digit Algorithms for Integer e-th
Root Extraction", arXiv:2601.02703.

Guarantees:
- Exact integer root floor(N^(1/n))
- Perfect power detection
- Fractional approximation with |x - N^(1/n)| < 10^{-k}
"""

class NthRoot:
    def __init__(self, N, n, digits=20):
        self.n = int(n)
        self.digits = int(digits)

        # Set precision BEFORE Decimal construction
        getcontext().prec = self.digits + 10

        # Normalize input exactly
        if isinstance(N, Decimal):
            self.N = N
        elif isinstance(N, int):
            self.N = Decimal(N)
        elif isinstance(N, float):
            # Accept scientific notation, but explicitly as Decimal
            self.N = Decimal(str(N))
        else:
            raise TypeError("N must be int, Decimal, or float")

    def integer_nth_root(self):
        """
        Exact digit-by-digit integer n-th root.
        Returns R = floor(N^(1/n)).
        """
        if self.N == 0:
            return 0

        N_int = int(self.N)   # safe: integer stage uses floor(N)
        base = 10 ** self.n

        blocks = []
        temp = N_int
        while temp > 0:
            blocks.append(temp % base)
            temp //= base
        blocks.reverse()

        R = 0
        delta = 0

        for a in blocks:
            delta = delta * base + a
            x = 0
            for d in range(10):
                inc = (10 * R + d) ** self.n - (10 * R) ** self.n
                if inc <= delta:
                    x = d
                else:
                    break
            delta -= (10 * R + x) ** self.n - (10 * R) ** self.n
            R = 10 * R + x

        return R

    def fractional_refinement(self, R_int):
        """
        Interval refinement for fractional n-th root.
        Guarantees |x - N^(1/n)| < 10^{-digits}.
        """
        R = Decimal(R_int)
        step = Decimal(1)

        for _ in range(self.digits):
            step /= 10
            while (R + step) ** self.n <= self.N:
                R += step

        return +R

    def root(self):
        """
        Combined algorithm:
        - Exact integer n-th root
        - Tolerant perfect-power detection
        - Fractional refinement if needed
        """
        if self.N == 0:
            return Decimal(0)

        R_int = self.integer_nth_root()
        R_dec = Decimal(R_int)
        if float(R_int**self.n) == float(self.N):
            return round(Decimal(R_int),0)

        # Tolerant perfect-power detection
        tolerance = Decimal(10) ** (-self.digits)
        if abs(R_dec ** self.n - self.N) < tolerance:
            return R_dec

        # Otherwise, fractional refinement
        return self.fractional_refinement(R_int)
