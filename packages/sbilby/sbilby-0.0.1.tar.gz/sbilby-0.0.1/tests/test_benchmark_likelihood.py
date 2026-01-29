import pytest
import numpy as np
from sbilby.simulation_based_inference_multidetector_realData import NLEResidualLikelihood_realData
import copy

class BenchmarkLikelihood(object):
    def __init__(
        self,
        nrle_likelihood,
        reference_likelihood,
        priors,
        reference_prior,
        outdir,
        injection_parameters,
        training_time,
    ):
        self.nrle_likelihood = nrle_likelihood
        self.reference_likelihood = reference_likelihood
        self.priors = priors
        self.reference_prior = reference_prior
        self.outdir = outdir
        self.injection_parameters = injection_parameters
        self.statistics = dict(
            likelihood_class=nrle_likelihood.__class__.__name__,
            likelihood_metadata=nrle_likelihood.meta_data,
        )
        self.training_time=training_time

    def _time_likelihood(self, likelihood, n, name):
        eval_times = []
        for _ in range(n):
            likelihood.parameters.update(self.priors.sample())
            start = time.time()
            likelihood.log_likelihood()
            end = time.time()
            eval_times.append(end - start)
        self.statistics[f"likelihood_{name}_eval_time_mean"] = float(
            np.mean(eval_times)
        )
        self.statistics[f"likelihood_{name}_eval_time_std"] = float(np.std(eval_times))

    def benchmark_time(self, n=100):
        self._time_likelihood(self.nrle_likelihood, n, "nrle")
        self._time_likelihood(self.reference_likelihood, n, "reference")
        self.statistics["likelihood_training_time"]=self.training_time
    def benchmark_posterior_sampling(self, run_sampler_kwargs=None):
        kwargs = dict(nlive=1000, sampler="dynesty", dlogz=0.5, check_point_delta_t=60)
        if run_sampler_kwargs is not None:
            kwargs.update(run_sampler_kwargs)

        result_reference = bilby.run_sampler(
            likelihood=self.reference_likelihood,
            priors=self.reference_prior,
            outdir=self.outdir,
            injection_parameters=injection_parameters,
            label=self.nrle_likelihood.labels[0] + "_REFERENCE",
            conversion_function=bilby.gw.conversion.generate_all_bbh_parameters,
            **kwargs,
        )

        result_nrle = bilby.run_sampler(
            likelihood=self.nrle_likelihood,
            priors=self.priors,
            outdir=self.outdir,
            injection_parameters=injection_parameters,
            label=self.nrle_likelihood.labels[0],
            #conversion_function=bilby.gw.conversion.generate_all_bbh_parameters,
            **kwargs,
        )

        for key, val in self.reference_prior.items():
            if val.is_fixed is False:
                samplesA = result_nrle.posterior[key]
                samplesB = result_reference.posterior[key]
                js = calculate_js(samplesA, samplesB)
                self.statistics[f"1D_posterior_JS_{key}_median"] = js.median
                self.statistics[f"1D_posterior_JS_{key}_plus"] = js.plus
                self.statistics[f"1D_posterior_JS_{key}_minus"] = js.minus

                fig, ax = plt.subplots()
                ax.hist(samplesA, bins=50, alpha=0.8, label="RNLE", density=True)
                ax.hist(samplesB, bins=50, alpha=0.8, label="Bilby", density=True)
                ax.axvline(self.injection_parameters[key], color="k")
                ax.set(xlabel=key, title=f"JS={js.median}")
                ax.legend()
                plt.savefig(
                        f"{self.outdir}/{self.nrle_likelihood.labels}_1D_posterior_{key}.png"
                )


    def write_results(self):
        bilby.utils.check_directory_exists_and_if_not_mkdir("RESULTS_real_data_injection")
        with open(
            f"RESULTS_real_data_injection/result_nrle_{self.nrle_likelihood.labels}.json", "w"
        ) as file:
            json.dump(self.statistics, file, indent=4)
# ------------------------------
# Fixtures for reusable objects
# ------------------------------
@pytest.fixture
def dummy_likelihood():
    """Create a small dummy likelihood object"""
    class DummyLikelihood:
        def __init__(self):
            self.parameters = {"sigma_h1": 1.0, "chirp_mass": 28}
            self.labels = ["test_label"]
            self.meta_data = {"info": "dummy"}
        def log_likelihood(self):
            return -0.5 * (self.parameters["chirp_mass"] - 28) ** 2
        def init(self):
            pass

    return DummyLikelihood()

@pytest.fixture
def dummy_prior():
    """Create a dummy prior dict"""
    class DummyPrior(dict):
        def sample(self):
            return {"chirp_mass": 28}
    return DummyPrior()

@pytest.fixture
def benchmark_obj(dummy_likelihood, dummy_prior):
    """Return a BenchmarkLikelihood instance with dummy likelihoods"""
    return BenchmarkLikelihood(
        nrle_likelihood=dummy_likelihood,
        reference_likelihood=dummy_likelihood,
        priors=dummy_prior,
        reference_prior=dummy_prior,
        outdir="tests_output",
        injection_parameters={"chirp_mass": 28},
        training_time=0.1,
    )

# ------------------------------
# Tests
# ------------------------------

def test_time_likelihood_runs(benchmark_obj):
    """Test that _time_likelihood computes stats without error"""
    benchmark_obj._time_likelihood(benchmark_obj.nrle_likelihood, n=5, name="nrle")
    assert "likelihood_nrle_eval_time_mean" in benchmark_obj.statistics
    assert isinstance(benchmark_obj.statistics["likelihood_nrle_eval_time_mean"], float)

def test_benchmark_time_runs(benchmark_obj):
    """Test benchmark_time sets expected statistics"""
    benchmark_obj.benchmark_time(n=5)
    assert "likelihood_nrle_eval_time_mean" in benchmark_obj.statistics
    assert "likelihood_reference_eval_time_mean" in benchmark_obj.statistics
    assert benchmark_obj.statistics["likelihood_training_time"] == benchmark_obj.training_time

def test_js_calculation_matches_expected():
    """Test JS calculation returns median, plus, minus"""
    from sbilby.examples.Polished_real_data_injection import calculate_js
    samplesA = np.random.normal(0, 1, 100)
    samplesB = np.random.normal(0, 1, 100)
    summary = calculate_js(samplesA, samplesB, ntests=5, xsteps=10)
    assert hasattr(summary, "median")
    assert hasattr(summary, "plus")
    assert hasattr(summary, "minus")
    assert isinstance(summary.median, float)

def test_write_results_creates_file(tmp_path, benchmark_obj):
    """Test write_results creates a JSON file"""
    benchmark_obj.outdir = tmp_path
    benchmark_obj.labels = ["test"]
    benchmark_obj.statistics = {"example_stat": 1}
    benchmark_obj.write_results()
    import json, os
    files = os.listdir("RESULTS_real_data_injection")
    assert any(f.endswith(".json") for f in files)

