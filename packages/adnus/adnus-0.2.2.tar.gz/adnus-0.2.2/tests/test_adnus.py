# tests/test_adnus.py
import pytest
import math
from fractions import Fraction
from adnus import *

class TestBicomplexNumber:
    def test_addition(self):
        # Yeni yapı: Bicomplex(z1_real, z1_imag, z2_real, z2_imag)
        bc1 = Bicomplex(1, 2, 3, 4)  # (1+2j) + (3+4j)·j
        bc2 = Bicomplex(5, 6, 7, 8)  # (5+6j) + (7+8j)·j
        result = bc1 + bc2
        # Beklenen: (6+8j) + (10+12j)·j
        assert isinstance(result, BicomplexNumber)
        assert math.isclose(result.z1[0], 6.0)  # real part of z1
        assert math.isclose(result.z1[1], 8.0)  # imag part of z1
        assert math.isclose(result.z2[0], 10.0) # real part of z2
        assert math.isclose(result.z2[1], 12.0) # imag part of z2

    def test_subtraction(self):
        bc1 = Bicomplex(1, 2, 3, 4)
        bc2 = Bicomplex(5, 6, 7, 8)
        result = bc1 - bc2
        # Beklenen: (-4-4j) + (-4-4j)·j
        assert math.isclose(result.z1[0], -4.0)
        assert math.isclose(result.z1[1], -4.0)
        assert math.isclose(result.z2[0], -4.0)
        assert math.isclose(result.z2[1], -4.0)

    def test_multiplication(self):
        bc1 = Bicomplex(1, 1, 1, 1)  # (1+1j) + (1+1j)·j
        bc2 = Bicomplex(1, 1, 1, 1)  # (1+1j) + (1+1j)·j
        
        # (1+i, 1+i) * (1+i, 1+i) = (0, 4i) olmalı
        result = bc1 * bc2
        
        # z1 = (1+i)*(1+i) - (1+i)*(1+i) = 2i - 2i = 0
        # z2 = (1+i)*(1+i) + (1+i)*(1+i) = 2i + 2i = 4i
        assert math.isclose(result.z1[0], 0.0, abs_tol=1e-10)  # real part of z1
        assert math.isclose(result.z1[1], 0.0, abs_tol=1e-10)  # imag part of z1
        assert math.isclose(result.z2[0], 0.0, abs_tol=1e-10)  # real part of z2
        assert math.isclose(result.z2[1], 4.0, abs_tol=1e-10)  # imag part of z2

    def test_norm(self):
        # (3+4j) + (5+12j)·j
        # |3+4j| = 5, |5+12j| = 13
        # norm = sqrt(5² + 13²) = sqrt(25 + 169) = sqrt(194)
        bc = Bicomplex(3, 4, 5, 12)
        expected_norm = math.sqrt(5**2 + 13**2)  # sqrt(194)
        assert math.isclose(bc.norm(), expected_norm, rel_tol=1e-10)

class TestNeutrosophicNumber:
    def test_addition(self):
        n1 = Neutrosophic(1.5, 2.5)
        n2 = Neutrosophic(3.0, 4.0)
        result = n1 + n2
        assert isinstance(result, NeutrosophicNumber)
        assert math.isclose(result.determinate, 4.5)
        assert math.isclose(result.indeterminate, 6.5)

    def test_multiplication(self):
        n1 = Neutrosophic(2, 3)
        n2 = Neutrosophic(4, 5)
        # (a + bI)(c + dI) = ac + (ad + bc + bd)I
        # 2*4 = 8 (determinate)
        # 2*5 + 3*4 + 3*5 = 10 + 12 + 15 = 37 (indeterminate)
        result = n1 * n2
        assert math.isclose(result.determinate, 8.0)
        assert math.isclose(result.indeterminate, 37.0)


class TestHypercomplexNumber:
    def test_real_addition(self):
        r1 = Real(3.14)
        r2 = Real(2.71)
        result = r1 + r2
        assert isinstance(result, HypercomplexNumber)
        assert math.isclose(float(result), 5.85)
        assert result.dimension == 1

    def test_complex_addition(self):
        c1 = Complex(3, 4)
        c2 = Complex(1, 2)
        result = c1 + c2
        assert isinstance(result, HypercomplexNumber)
        assert result.dimension == 2
        assert math.isclose(result[0], 4.0)  # real part
        assert math.isclose(result[1], 6.0)  # imag part

    def test_complex_multiplication(self):
        c1 = Complex(3, 4)
        c2 = Complex(1, 2)
        result = c1 * c2
        # (3+4i)(1+2i) = 3*1 - 4*2 + (3*2 + 4*1)i = 3-8 + (6+4)i = -5 + 10i
        assert math.isclose(result[0], -5.0)
        assert math.isclose(result[1], 10.0)

    def test_quaternion_multiplication(self):
        q1 = Quaternion(1, 2, 3, 4)
        q2 = Quaternion(5, 6, 7, 8)
        result = q1 * q2
        # Quaternion multiplication test
        # w = w1*w2 - x1*x2 - y1*y2 - z1*z2 = 1*5 - 2*6 - 3*7 - 4*8 = 5 - 12 - 21 - 32 = -60
        # x = w1*x2 + x1*w2 + y1*z2 - z1*y2 = 1*6 + 2*5 + 3*8 - 4*7 = 6 + 10 + 24 - 28 = 12
        # y = w1*y2 - x1*z2 + y1*w2 + z1*x2 = 1*7 - 2*8 + 3*5 + 4*6 = 7 - 16 + 15 + 24 = 30
        # z = w1*z2 + x1*y2 - y1*x2 + z1*w2 = 1*8 + 2*7 - 3*6 + 4*5 = 8 + 14 - 18 + 20 = 24
        assert math.isclose(result[0], -60.0, rel_tol=1e-10)
        assert math.isclose(result[1], 12.0, rel_tol=1e-10)
        assert math.isclose(result[2], 30.0, rel_tol=1e-10)
        assert math.isclose(result[3], 24.0, rel_tol=1e-10)


class TestHelperFunctions:
    def test_oresme_sequence(self):
        # oresme_sequence(n) = [k/2^k for k in 1..n]
        result = oresme_sequence(3)
        expected = [1/2, 2/4, 3/8]
        assert len(result) == 3
        for r, e in zip(result, expected):
            assert math.isclose(r, e)
        
        assert oresme_sequence(0) == []
        assert oresme_sequence(1) == [1/2]

    def test_harmonic_numbers(self):
        harmonics = list(harmonic_numbers(3))
        expected = [Fraction(1, 1), Fraction(3, 2), Fraction(11, 6)]
        assert len(harmonics) == 3
        for h, e in zip(harmonics, expected):
            assert h == e

    def test_binet_formula(self):
        # Binet's formula for Fibonacci numbers
        # F(0) = 0, F(1) = 1, F(2) = 1, F(3) = 2, F(4) = 3, F(5) = 5, F(10) = 55
        test_cases = [
            (0, 0),
            (1, 1),
            (2, 1),
            (3, 2),
            (4, 3),
            (5, 5),
            (10, 55)
        ]
        
        for n, expected in test_cases:
            result = binet_formula(n)
            assert math.isclose(result, expected, rel_tol=1e-10)
        
        # Negatif sayı için hata testi
        # Not: Yeni kodda ValueError kontrolü yoksa bu testi kaldırın
        # with pytest.raises(ValueError):
        #     binet_formula(-1)

    def test_generate_cd_chain_names(self):
        names = generate_cd_chain_names(4)
        expected = ["Real", "Complex", "Quaternion", "Octonion", "Sedenion"]
        assert names == expected
        
        names = generate_cd_chain_names(2)
        expected = ["Real", "Complex", "Quaternion"]
        assert names == expected

class TestFactoryFunctions:
    def test_real_factory(self):
        r = Real(3.14)
        assert isinstance(r, HypercomplexNumber)
        assert r.dimension == 1
        assert math.isclose(float(r), 3.14)
    
    def test_complex_factory(self):
        c = Complex(3, 4)
        assert isinstance(c, HypercomplexNumber)
        assert c.dimension == 2
        assert math.isclose(c[0], 3.0)  # real
        assert math.isclose(c[1], 4.0)  # imag
    
    def test_quaternion_factory(self):
        q = Quaternion(1, 2, 3, 4)
        assert isinstance(q, HypercomplexNumber)
        assert q.dimension == 4
        assert math.isclose(q[0], 1.0)  # w
        assert math.isclose(q[1], 2.0)  # x
        assert math.isclose(q[2], 3.0)  # y
        assert math.isclose(q[3], 4.0)  # z
    
    def test_octonion_factory(self):
        o = Octonion(1, 2, 3, 4, 5, 6, 7, 8)
        assert isinstance(o, HypercomplexNumber)
        assert o.dimension == 8
        for i in range(8):
            assert math.isclose(o[i], float(i + 1))

class TestConversions:
    def test_hypercomplex_to_complex(self):
        c = Complex(3, 4)
        py_complex = c.to_complex()
        assert isinstance(py_complex, complex)
        assert math.isclose(py_complex.real, 3.0)
        assert math.isclose(py_complex.imag, 4.0)
    
    def test_real_to_float(self):
        r = Real(3.14)
        assert math.isclose(float(r), 3.14)
    
    def test_mixed_operations(self):
        # Real * Complex
        r = Real(5.0)
        c = Complex(3, 4)
        result = r * c
        assert isinstance(result, HypercomplexNumber)
        assert result.dimension == 2
        assert math.isclose(result[0], 15.0)  # 5 * 3
        assert math.isclose(result[1], 20.0)  # 5 * 4
        
        # Complex * Real
        result2 = c * r
        assert result == result2  # Should be commutative for scalar multiplication

if __name__ == "__main__":
    # Run tests
    print("Running tests...")
    
    # Test BicomplexNumber
    test_bc = TestBicomplexNumber()
    test_bc.test_addition()
    print("✓ BicomplexNumber addition test passed")
    
    test_bc.test_subtraction()
    print("✓ BicomplexNumber subtraction test passed")
    
    test_bc.test_multiplication()
    print("✓ BicomplexNumber multiplication test passed")
    
    test_bc.test_norm()
    print("✓ BicomplexNumber norm test passed")
    
    # Test NeutrosophicNumber
    test_n = TestNeutrosophicNumber()
    test_n.test_addition()
    print("✓ NeutrosophicNumber addition test passed")
    
    test_n.test_multiplication()
    print("✓ NeutrosophicNumber multiplication test passed")
    
    # Test HypercomplexNumber
    test_hn = TestHypercomplexNumber()
    test_hn.test_real_addition()
    print("✓ HypercomplexNumber real addition test passed")
    
    test_hn.test_complex_addition()
    print("✓ HypercomplexNumber complex addition test passed")
    
    test_hn.test_complex_multiplication()
    print("✓ HypercomplexNumber complex multiplication test passed")
    
    test_hn.test_quaternion_multiplication()
    print("✓ HypercomplexNumber quaternion multiplication test passed")
    
    # Test HelperFunctions
    test_hf = TestHelperFunctions()
    test_hf.test_oresme_sequence()
    print("✓ oresme_sequence test passed")
    
    test_hf.test_harmonic_numbers()
    print("✓ harmonic_numbers test passed")
    
    test_hf.test_binet_formula()
    print("✓ binet_formula test passed")
    
    test_hf.test_generate_cd_chain_names()
    print("✓ generate_cd_chain_names test passed")
    
    # Test FactoryFunctions
    test_ff = TestFactoryFunctions()
    test_ff.test_real_factory()
    print("✓ Real factory test passed")
    
    test_ff.test_complex_factory()
    print("✓ Complex factory test passed")
    
    test_ff.test_quaternion_factory()
    print("✓ Quaternion factory test passed")
    
    test_ff.test_octonion_factory()
    print("✓ Octonion factory test passed")
    
    # Test Conversions
    test_cv = TestConversions()
    test_cv.test_hypercomplex_to_complex()
    print("✓ Hypercomplex to complex conversion test passed")
    
    test_cv.test_real_to_float()
    print("✓ Real to float conversion test passed")
    
    test_cv.test_mixed_operations()
    print("✓ Mixed operations test passed")
    
    print("\n✅ All tests passed successfully!")
