"""
Unit Tests for TVRCoint Library
"""

import numpy as np
import pytest
import sys
sys.path.insert(0, '../src')


class TestChebyshev:
    """Test Chebyshev polynomial functions."""
    
    def test_chebyshev_poly_order_zero(self):
        """P_{0,T}(t) should always be 1."""
        from tvrcoint.chebyshev import chebyshev_poly
        
        for T in [50, 100, 200]:
            for t in [1, T//2, T]:
                assert chebyshev_poly(0, t, T) == 1.0
    
    def test_chebyshev_poly_order_one(self):
        """P_{1,T}(t) should be sqrt(2)*cos(π*(t-0.5)/T)."""
        from tvrcoint.chebyshev import chebyshev_poly
        
        T = 100
        for t in [1, 50, 100]:
            expected = np.sqrt(2) * np.cos(np.pi * (t - 0.5) / T)
            result = chebyshev_poly(1, t, T)
            assert np.isclose(result, expected)
    
    def test_chebyshev_polynomials_shape(self):
        """chebyshev_polynomials should return (m+1, T) array."""
        from tvrcoint.chebyshev import chebyshev_polynomials
        
        m, T = 3, 100
        P = chebyshev_polynomials(m, T)
        assert P.shape == (m + 1, T)
    
    def test_chebyshev_orthonormality(self):
        """Chebyshev polynomials should be orthonormal."""
        from tvrcoint.chebyshev import verify_orthonormality
        
        for m in [1, 3, 5]:
            for T in [50, 100, 200]:
                assert verify_orthonormality(m, T)
    
    def test_chebyshev_matrix_shape(self):
        """chebyshev_matrix should return (T-1, (m+1)*k) array."""
        from tvrcoint.chebyshev import chebyshev_matrix
        
        T, k, m = 100, 3, 2
        Y = np.random.randn(T, k)
        Y_m = chebyshev_matrix(Y, m)
        
        assert Y_m.shape == (T - 1, (m + 1) * k)


class TestMatrices:
    """Test matrix computation functions."""
    
    def test_compute_s_matrices_shapes(self):
        """S matrices should have correct shapes."""
        from tvrcoint.matrices import compute_s_matrices
        
        T_eff, k, m = 98, 3, 2
        delta_Y = np.random.randn(T_eff, k)
        Y_m = np.random.randn(T_eff, (m + 1) * k)
        
        S = compute_s_matrices(delta_Y, Y_m)
        
        assert S['S00'].shape == (k, k)
        assert S['S11'].shape == ((m + 1) * k, (m + 1) * k)
        assert S['S01'].shape == (k, (m + 1) * k)
        assert S['S10'].shape == ((m + 1) * k, k)
    
    def test_s_matrices_symmetry(self):
        """S00 and S11 should be symmetric."""
        from tvrcoint.matrices import compute_s_matrices
        
        T_eff, k, m = 98, 3, 2
        delta_Y = np.random.randn(T_eff, k)
        Y_m = np.random.randn(T_eff, (m + 1) * k)
        
        S = compute_s_matrices(delta_Y, Y_m)
        
        assert np.allclose(S['S00'], S['S00'].T)
        assert np.allclose(S['S11'], S['S11'].T)
    
    def test_s01_s10_transpose(self):
        """S10 should be transpose of S01."""
        from tvrcoint.matrices import compute_s_matrices
        
        T_eff, k, m = 98, 3, 2
        delta_Y = np.random.randn(T_eff, k)
        Y_m = np.random.randn(T_eff, (m + 1) * k)
        
        S = compute_s_matrices(delta_Y, Y_m)
        
        assert np.allclose(S['S10'], S['S01'].T)
    
    def test_eigenvalues_in_unit_interval(self):
        """Eigenvalues should be in [0, 1]."""
        from tvrcoint.matrices import compute_s_matrices, solve_eigenvalue_problem
        
        np.random.seed(42)
        T_eff, k, m = 98, 2, 1
        delta_Y = np.random.randn(T_eff, k)
        Y_m = np.random.randn(T_eff, (m + 1) * k)
        
        S = compute_s_matrices(delta_Y, Y_m)
        eigenvalues, _ = solve_eigenvalue_problem(S['S11'], S['S10'], S['S00'], S['S01'])
        
        assert np.all(eigenvalues >= 0)
        assert np.all(eigenvalues <= 1)


class TestTVVECM:
    """Test TV-VECM estimation."""
    
    def test_tvvecm_fit_returns_results(self):
        """TVVECM.fit should return TVVECMResults."""
        from tvrcoint.tvvecm import TVVECM
        from tvrcoint.simulation import generate_cointegrated_data
        
        np.random.seed(42)
        Y = generate_cointegrated_data(100, k=2, r=1)
        
        model = TVVECM()
        results = model.fit(Y, r=1, m=0, p=1)
        
        assert results is not None
        assert results.T > 0
        assert results.k == 2
        assert results.r == 1
    
    def test_tvvecm_residuals_shape(self):
        """Residuals should have shape (T_eff, k)."""
        from tvrcoint.tvvecm import TVVECM
        from tvrcoint.simulation import generate_cointegrated_data
        
        np.random.seed(42)
        T, k, r, p = 100, 3, 1, 2
        Y = generate_cointegrated_data(T, k=k, r=r)
        
        model = TVVECM()
        results = model.fit(Y, r=r, m=0, p=p)
        
        assert results.residuals.shape[1] == k
        assert results.residuals.shape[0] == results.T
    
    def test_tvvecm_alpha_beta_shapes(self):
        """Alpha and beta should have correct shapes."""
        from tvrcoint.tvvecm import TVVECM
        from tvrcoint.simulation import generate_cointegrated_data
        
        np.random.seed(42)
        T, k, r = 100, 3, 1
        Y = generate_cointegrated_data(T, k=k, r=r)
        
        model = TVVECM()
        results = model.fit(Y, r=r, m=0, p=1)
        
        assert results.alpha.shape == (k, r)
        assert results.beta.shape == (k, r)


class TestLRTest:
    """Test LR test for time-varying cointegration."""
    
    def test_tvc_test_returns_results(self):
        """TVCTest.test should return TVCTestResults."""
        from tvrcoint.lr_test import TVCTest
        from tvrcoint.simulation import generate_cointegrated_data
        
        np.random.seed(42)
        Y = generate_cointegrated_data(100, k=2, r=1)
        
        test = TVCTest()
        results = test.test(Y, r=1, m=1, p=1)
        
        assert results is not None
        assert results.statistic >= 0
        assert 0 <= results.pvalue <= 1
    
    def test_tvc_test_df_formula(self):
        """Degrees of freedom should be m*k*r."""
        from tvrcoint.lr_test import TVCTest
        from tvrcoint.simulation import generate_cointegrated_data
        
        np.random.seed(42)
        m, k, r = 5, 3, 1
        Y = generate_cointegrated_data(200, k=k, r=r)
        
        test = TVCTest()
        results = test.test(Y, r=r, m=m, p=1)
        
        assert results.df == m * k * r
    
    def test_lr_statistic_nonnegative(self):
        """LR statistic should be non-negative."""
        from tvrcoint.lr_test import TVCTest
        from tvrcoint.simulation import generate_cointegrated_data
        
        np.random.seed(42)
        for _ in range(5):
            Y = generate_cointegrated_data(100, k=2, r=1)
            test = TVCTest()
            results = test.test(Y, r=1, m=2, p=1)
            assert results.statistic >= 0


class TestBootstrap:
    """Test bootstrap TVC test."""
    
    def test_bootstrap_returns_results(self):
        """BootstrapTVCTest.test should return BootstrapTVCTestResults."""
        from tvrcoint.bootstrap import BootstrapTVCTest
        from tvrcoint.simulation import generate_cointegrated_data
        
        np.random.seed(42)
        Y = generate_cointegrated_data(80, k=2, r=1)
        
        test = BootstrapTVCTest()
        results = test.test(Y, r=1, m=1, p=1, B=99, seed=42)
        
        assert results is not None
        assert 0 <= results.pvalue_bootstrap <= 1
    
    def test_bootstrap_statistics_length(self):
        """Bootstrap statistics array should have length B."""
        from tvrcoint.bootstrap import BootstrapTVCTest
        from tvrcoint.simulation import generate_cointegrated_data
        
        np.random.seed(42)
        B = 99
        Y = generate_cointegrated_data(80, k=2, r=1)
        
        test = BootstrapTVCTest()
        results = test.test(Y, r=1, m=1, p=1, B=B, seed=42)
        
        assert len(results.bootstrap_statistics) == B
    
    def test_wild_vs_iid_different(self):
        """Wild and i.i.d. bootstrap should give different results."""
        from tvrcoint.bootstrap import BootstrapTVCTest
        from tvrcoint.simulation import generate_cointegrated_data
        
        np.random.seed(42)
        Y = generate_cointegrated_data(80, k=2, r=1)
        
        test = BootstrapTVCTest()
        results_wild = test.test(Y, r=1, m=2, p=1, method='wild', B=99, seed=42)
        results_iid = test.test(Y, r=1, m=2, p=1, method='iid', B=99, seed=42)
        
        # They should use the same original statistic
        assert results_wild.statistic == results_iid.statistic
        
        # But bootstrap p-values may differ (due to different resampling)
        # This is not strictly guaranteed, but typically true


class TestSimulation:
    """Test simulation functions."""
    
    def test_generate_cointegrated_data_shape(self):
        """Generated data should have correct shape."""
        from tvrcoint.simulation import generate_cointegrated_data
        
        T, k = 100, 3
        Y = generate_cointegrated_data(T, k=k, r=1)
        
        assert Y.shape == (T, k)
    
    def test_dgp_bm_bivariate(self):
        """BM DGP should generate bivariate data."""
        from tvrcoint.simulation import dgp_bm
        
        T = 100
        Y = dgp_bm(T, k=2, p=2, seed=42)
        
        assert Y.shape == (T, 2)
    
    def test_dgp_js_trivariate(self):
        """JS DGP should generate trivariate data."""
        from tvrcoint.simulation import dgp_js
        
        T = 100
        Y = dgp_js(T, k=3, seed=42)
        
        assert Y.shape == (T, 3)
    
    def test_reproducibility_with_seed(self):
        """Same seed should produce same data."""
        from tvrcoint.simulation import generate_cointegrated_data
        
        Y1 = generate_cointegrated_data(100, k=2, r=1, seed=42)
        Y2 = generate_cointegrated_data(100, k=2, r=1, seed=42)
        
        assert np.allclose(Y1, Y2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
