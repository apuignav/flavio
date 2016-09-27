import numpy as np
import scipy.stats
import scipy.interpolate
import scipy.signal
import math


########## ProbabilityDistribution Class ##########
class ProbabilityDistribution(object):
   """Common base class for all probability distributions"""

   def __init__(self, central_value, support):
      self.central_value = central_value
      self.support = support

   def get_central(self):
      return self.central_value

    # here we define the __hash__ and __eq__ methods to be able to use
    # instances as dictionary keys.

   def __hash__(self):
      return id(self)

   def __eq__(self, other):
      return id(self) == id(other)



class UniformDistribution(ProbabilityDistribution):

   def __init__(self, central_value, half_range):
      self.half_range = half_range
      self.range = (self.central_value - self.half_range,
                    self.central_value + self.half_range)
      super().__init__(central_value, support=self.range)

   def get_random(self, size=None):
      return np.random.uniform(self.range[0], self.range[1], size)

   def logpdf(self, x):
       if x < self.range[0] or x >= self.range[1]:
           return 0
       else:
           return -math.log(2*self.half_range)

class DeltaDistribution(ProbabilityDistribution):
   def __init__(self, central_value):
      super().__init__(central_value, support=(central_value, central_value))

   def get_random(self, size=None):
      if size is None:
          return self.central_value
      else:
          return self.central_value * np.ones(size)

   def logpdf(self, x):
       if x == self.central_value:
           return 0.
       else:
           return -np.inf

class NormalDistribution(ProbabilityDistribution):

   def __init__(self, central_value, standard_deviation):
      super().__init__(central_value,
                      support=(central_value-6*standard_deviation,
                               central_value+6*standard_deviation))
      self.standard_deviation = standard_deviation

   def get_random(self, size=None):
      return np.random.normal(self.central_value, self.standard_deviation, size)

   def logpdf(self, x):
       return scipy.stats.norm.logpdf(x, self.central_value, self.standard_deviation)

class AsymmetricNormalDistribution(ProbabilityDistribution):

   def __init__(self, central_value, right_deviation, left_deviation):
      super().__init__(central_value,
                       support=(central_value-6*left_deviation,
                                central_value+6*right_deviation))
      if right_deviation < 0 or left_deviation < 0:
          raise ValueError("Left and right standard deviations must be positive numbers")
      self.right_deviation = right_deviation
      self.left_deviation = left_deviation

   def get_random(self, size=None):
        r = np.random.uniform()
        a = abs(self.left_deviation/(self.right_deviation+self.left_deviation))
        if  r > a:
            x = abs(np.random.normal(0,self.right_deviation))
            return self.central_value + x
        else:
            x = abs(np.random.normal(0,self.left_deviation))
            return self.central_value - x

   def _logpdf(self, x):
       # values of the PDF at the central value
       p_right = scipy.stats.norm.pdf(self.central_value, self.central_value, self.right_deviation)
       p_left = scipy.stats.norm.pdf(self.central_value, self.central_value, self.left_deviation)
       if x < self.central_value:
           # left-hand side: scale factor
           r = 2*p_right/(p_left+p_right)
           return math.log(r) + scipy.stats.norm.logpdf(x, self.central_value, self.left_deviation)
       else:
           # left-hand side: scale factor
           r = 2*p_left/(p_left+p_right)
           return math.log(r) + scipy.stats.norm.logpdf(x, self.central_value, self.right_deviation)

   def logpdf(self, x):
        _lpvect = np.vectorize(self._logpdf)
        return _lpvect(x)

class HalfNormalDistribution(ProbabilityDistribution):

   def __init__(self, central_value, standard_deviation):
      super().__init__(central_value,
                       support=sorted((central_value,
                                       central_value+6*standard_deviation)))
      self.standard_deviation = standard_deviation

   def get_random(self, size=None):
      return self.central_value + np.sign(self.standard_deviation)*abs(np.random.normal(0, abs(self.standard_deviation), size))

   def _logpdf(self, x):
       if np.sign(self.standard_deviation) * (x - self.central_value) < 0:
           return -np.inf
       else:
           return math.log(2) + scipy.stats.norm.logpdf(x, self.central_value, abs(self.standard_deviation))

   def logpdf(self, x):
        _lpvect = np.vectorize(self._logpdf)
        return _lpvect(x)

class GaussianUpperLimit(HalfNormalDistribution):
   def __init__(self, limit, confidence_level):
      if confidence_level > 1 or confidence_level < 0:
          raise ValueError("Confidence level should be between 0 und 1")
      super().__init__(central_value=0,
                       standard_deviation=self.get_standard_deviation(limit, confidence_level))
      self.limit = limit
      self.confidence_level = confidence_level

   def get_standard_deviation(self, limit, confidence_level):
       """Convert the confidence level into a Gaussian standard deviation"""
       return limit*scipy.stats.norm.ppf(0.5+confidence_level/2.)

class NumericalDistribution(ProbabilityDistribution):
   def __init__(self, x, y, central_value=None):
      if central_value is not None:
          if x[0] <= central_value <= x[-1]:
              super().__init__(central_value=central_value, support=(x[0], x[-1]))
          else:
              raise ValueError("Central value must be within range provided")
      else:
          mode = x[np.argmax(y)]
          super().__init__(central_value=mode, support=(x[0], x[-1]))
      _x_range = (x[-1]-x[0])
      _y_norm = y/sum(y)*_x_range # normalize PDF to 1
      self.logpdf_interp = scipy.interpolate.interp1d(x, np.log(_y_norm), fill_value=-np.inf)
      _cdf = np.cumsum(_y_norm)/_x_range
      # adapt the borders of the PPF to be 0 and 1
      _cdf[0] = 0.
      _cdf[-1] = 1.
      self.ppf_interp = scipy.interpolate.interp1d(_cdf, x)

   def get_random(self, size=None):
      r = np.random.uniform(size=size)
      return self.ppf_interp(r)

   def logpdf(self, x):
       return self.logpdf_interp(x)

class MultivariateNormalDistribution(ProbabilityDistribution):

   def __init__(self, central_value, covariance):
      super().__init__(central_value, support=None)
      assert np.all(np.linalg.eigvals(covariance) > 0), "The covariance matrix is not positive definite!" + str(covariance)
      self.covariance = covariance

   def get_random(self, size=None):
      return np.random.multivariate_normal(self.central_value, self.covariance, size)

   def logpdf(self, x):
       # to avoid ill-conditioned covariance matrices, all data are rescaled
       # by the inverse variances
       err = np.sqrt(np.diag(self.covariance))
       scale_matrix = np.outer(err, err)
       pdf_scaled = scipy.stats.multivariate_normal.logpdf(x/err, self.central_value/err, self.covariance/scale_matrix)
       return pdf_scaled + math.log(np.linalg.det(self.covariance/scale_matrix)/np.linalg.det(self.covariance))/2.




# Auxiliary functions

def convolute_distributions(probability_distributions):
    """Combine a set of univariate probability distributions.

    This function is meant for combining uncertainties on a single parameter/
    observable. As an argument, it takes a list of probability distributions
    that all have the same central value. It returns their convolution, but
    with location equal to the original central value.

    At present, this function is only implemented for univariate normal
    distributions.
    """
    # if there's just one: return it immediately
    if len(probability_distributions) == 1:
        return probability_distributions[0]
    central_value = probability_distributions[0].central_value # central value of the first dist
    assert isinstance(central_value, float), "Combination only implemented for univariate distributions"
    assert all(p.central_value == central_value for p in probability_distributions), \
        "Distrubtions must all have the same central value"
    # all normal dists
    gaussians = [p for p in probability_distributions if isinstance(p, NormalDistribution)]
    # let's alrady combined the normal distributions into 1
    gaussian = _convolute_gaussians(gaussians)
    # all delta dists -  they can be ignored!
    deltas = [p for p in probability_distributions if isinstance(p, DeltaDistribution)]
    # all other univariate dists
    others = list(set(probability_distributions) - set(gaussians) - set(deltas))
    if not others:
        # if there are only the gaussians, we are done.
        return gaussian
    else:
        raise ValueError("Combination only implemented for normal distributions")

def _convolute_gaussians(probability_distributions):
    assert all(isinstance(p, NormalDistribution) for p in probability_distributions), \
        "Distributions should all be instances of NormalDistribution"
    central_value = probability_distributions[0].central_value # central value of the first dist
    assert all(p.central_value == central_value for p in probability_distributions), \
        "Distrubtions must all have the same central value"
    sigmas = np.array([p.standard_deviation for p in probability_distributions])
    sigma = math.sqrt(np.sum(sigmas**2))
    return NormalDistribution(central_value=central_value, standard_deviation=sigma)
