"""A simple local MCP server that exposes tools for beta-binomial Bayesian modeling.

To run the server, execute the following command in your terminal:

    ```sh
    uv run fastmcp run 3-mcp-fundamentals/1-bayesian-tools/server.py:mcp --transport http --port 8000
    ```
"""

import math
from typing import Literal, Self, get_args

from fastmcp import FastMCP
from pydantic import BaseModel, Field, model_validator
from scipy import stats

# Models and function
type ConvictionLevel = Literal[
    "random",
    "gut feeling",
    "educated guess",
    "reasonably confident",
    "very confident",
    "bet the farm",
]

CONVICTION_TO_SAMPLE_SIZE = {
    "random guess": 1,
    "gut feeling": 7,
    "educated guess": 20,
    "reasonably confident": 50,
    "very confident": 100,
    "bet the farm": 1000,
}


class BetaParameters(BaseModel):
    """Parameters of a Beta distribution."""

    alpha: float = Field(
        description=(
            "Alpha parameter of the Beta distribution, representing number of 'successes'. Must be greater than 0."
        ),
        gt=0,
    )
    beta: float = Field(
        description=(
            "Beta parameter of the Beta distribution, representing number of 'failures'. Must be greater than 0."
        ),
        gt=0,
    )


class ConfidenceInterval(BaseModel):
    """Confidence interval for a probability distribution."""

    confidence_level: float = Field(
        description="Confidence level of the interval (e.g., 0.95 for 95% confidence).",
        gt=0.0,
        lt=1.0,
    )
    lower_bound: float = Field(
        description="Lower bound of the confidence interval.",
        ge=0.0,
        le=1.0,
    )
    upper_bound: float = Field(
        description="Upper bound of the confidence interval.",
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def check_lower_bound_less_than_upper_bound(self) -> Self:
        """Validate that lower_bound is strictly less than upper_bound."""
        if self.lower_bound >= self.upper_bound:
            raise ValueError(
                f"lower_bound ({self.lower_bound}) must be strictly less than upper_bound ({self.upper_bound})"
            )
        return self


class SampleDraw(BaseModel):
    """Result of drawing samples from a Beta-Binomial model."""

    num_samples: int = Field(
        description="Number of samples drawn.",
        gt=0,
    )
    num_successes: int = Field(
        description="Number of successful samples (True values).",
        ge=0,
    )
    num_failures: int = Field(
        description="Number of failed samples (False values).",
        ge=0,
    )
    success_rate: float = Field(
        description="Proportion of successful samples (num_successes / num_samples).",
        ge=0.0,
        le=1.0,
    )
    average_probability_of_success: float = Field(
        description="Average probability of success across all samples.",
        ge=0.0,
        le=1.0,
    )
    outcomes: list[bool] = Field(
        description="List of boolean outcomes from the samples.",
        min_length=1,
    )
    probabilities: list[float] = Field(
        description="List of probabilities associated with each sample.",
        min_length=1,
    )

    @model_validator(mode="after")
    def check_num_samples_agree(self) -> Self:
        """Validate that num_samples is consistent across all fields."""
        if self.num_samples != self.num_successes + self.num_failures:
            raise ValueError(
                f"num_samples ({self.num_samples}) must be equal to the sum of"
                f" num_successes ({self.num_successes}) and num_failures ({self.num_failures})"
            )
        if len(self.outcomes) != self.num_samples:
            raise ValueError(f"len(outcomes) ({len(self.outcomes)}) must be equal to num_samples ({self.num_samples})")
        if len(self.probabilities) != self.num_samples:
            raise ValueError(
                f"len(probabilities) ({len(self.probabilities)}) must be equal to num_samples ({self.num_samples})"
            )
        return self

    @model_validator(mode="after")
    def check_success_rate(self) -> Self:
        """Validate that success_rate is consistent with num_successes and num_samples."""
        expected_success_rate = self.num_successes / self.num_samples
        if not math.isclose(self.success_rate, expected_success_rate, rel_tol=1e-6):
            raise ValueError(
                f"success_rate ({self.success_rate}) must be equal to"
                f" num_successes / num_samples ({expected_success_rate})"
            )
        return self

    @model_validator(mode="after")
    def check_average_probability_of_success(self) -> Self:
        """Validate that average_probability_of_success is consistent with probabilities."""
        expected_average = sum(self.probabilities) / self.num_samples
        if not math.isclose(self.average_probability_of_success, expected_average, rel_tol=1e-6):
            raise ValueError(
                f"average_probability_of_success ({self.average_probability_of_success}) must be equal to"
                f" the average of probabilities ({expected_average})"
            )
        return self

    @classmethod
    def create(
        cls,
        outcomes: list[bool],
        probabilities: list[float],
    ) -> Self:
        """Create a SampleDraw instance from outcomes and probabilities.

        Args:
            outcomes (list[bool]): List of boolean outcomes from the samples.
            probabilities (list[float]): List of probabilities associated with each sample.

        Returns:
            Self: The created SampleDraw instance.
        """
        num_samples = len(outcomes)
        num_successes = sum(outcomes)
        num_failures = num_samples - num_successes
        return cls(
            num_samples=num_samples,
            num_successes=num_successes,
            num_failures=num_failures,
            success_rate=num_successes / num_samples,
            average_probability_of_success=sum(probabilities) / num_samples,
            outcomes=outcomes,
            probabilities=probabilities,
        )


def _get_implied_sample_size(conviction: ConvictionLevel, adjustment: float = 1.0) -> float:
    """Get the implied sample size based on conviction level."""
    if conviction not in CONVICTION_TO_SAMPLE_SIZE:
        raise ValueError(f"conviction must be one of {list(CONVICTION_TO_SAMPLE_SIZE.keys())}")

    if adjustment <= 0:
        raise ValueError("adjustment must be greater than 0.")

    return CONVICTION_TO_SAMPLE_SIZE[conviction] * adjustment


# MCP Server Setup
# Initialize the MCP server
mcp = FastMCP(name="Bayes Rules! Beta-Binomial Bayesian Modeling")


# Define tools
@mcp.tool()
def calculate_confidence_interval(
    beta_params: BetaParameters,
    confidence_level: float = 0.95,
) -> ConfidenceInterval:
    """Calculate the confidence interval for a beta distribution.

    Args:
        beta_params (BetaParameters): The parameters of the beta distribution.
        confidence_level (float): The desired confidence level (between 0 and 1). Defaults to 0.95.

    Returns:
        ConfidenceInterval: The calculated confidence interval.

    Raises:
        ValueError: If confidence_level is not between 0 and 1.

    Examples:
        Calculate the 95% confidence interval for a Beta(12.0, 8.0) distribution:
        >>> beta_params = BetaParameters(alpha=12.0, beta=8.0)
        >>> calculate_confidence_interval(beta_params, confidence_level=0.95)
        ConfidenceInterval(confidence_level=0.95, lower_bound=0.404, upper_bound=0.748)
    """
    # Validate confidence level
    if not (0.0 <= confidence_level <= 1.0):
        raise ValueError(f"confidence_level must be between 0 and 1; got {confidence_level}.")

    # Calculate the confidence interval using the beta distribution
    lower_bound, upper_bound = stats.beta(a=beta_params.alpha, b=beta_params.beta).interval(confidence_level)

    return ConfidenceInterval(
        confidence_level=confidence_level,
        lower_bound=lower_bound.item(),
        upper_bound=upper_bound.item(),
    )


@mcp.tool()
def get_beta_prior_from_beliefs(
    prior_probability: float,
    *,
    conviction: ConvictionLevel = "random",
    conviction_adjustment: float = 1.0,
) -> BetaParameters:
    """Derive the parameters of a beta prior from a prior probability and conviction level.

    This function uses an implied sample size based on the conviction level to calculate
    the alpha and beta parameters of the beta distribution that represents the prior belief.

    Args:
        prior_probability (float): The prior probability (between 0 and 1).
        conviction (ConvictionLevel): The level of conviction in the prior. Defaults to "random".
        conviction_adjustment (float): A multiplier to adjust the implied sample size. Must be greater than 0.
            Defaults to 1.0.

    Returns:
        BetaParameters: The parameters of the beta prior.

    Raises:
        ValueError: If prior_probability is not between 0 and 1.

    Examples:
        Infer a beta prior with a prior probability of 0.6 and "educated guess" conviction level (20 observations):
        >>> get_beta_prior_from_beliefs(0.6, conviction="educated guess")
        BetaParameters(alpha=12.0, beta=8.0)

        Tweak the conviction level to slightly less than "educated guess" (16 observations) using the adjustment factor:
        >>> get_beta_prior_from_beliefs(0.6, conviction="educated guess", conviction_adjustment=0.8)
        BetaParameters(alpha=9.6, beta=6.4)
    """
    if not (0 < prior_probability < 1):
        raise ValueError(
            f"prior_probability must be between 0 and 1. It cannot be exactly 0 or 1. Got {prior_probability}."
        )

    # Determine implied sample size based on conviction level
    sample_size = _get_implied_sample_size(conviction, adjustment=conviction_adjustment)

    # Calculate alpha and beta parameters from prior probability and sample size
    alpha = prior_probability * sample_size
    beta = (1 - prior_probability) * sample_size

    return BetaParameters(alpha=alpha, beta=beta)


@mcp.tool()
def get_implied_sample_size(conviction: ConvictionLevel, adjustment: float = 1.0) -> float:
    """Get the implied sample size based on conviction level.

    This function is useful for translating subjective conviction levels into
    quantitative sample sizes for Bayesian prior elicitation.

    Args:
        conviction (ConvictionLevel): The level of conviction in the prior.
        adjustment (float): A multiplier to adjust the implied sample size. Defaults to 1.0.

    Returns:
        float: The implied sample size corresponding to the conviction level.

    Examples:
        Get the implied sample size for "educated guess" conviction level:
        >>> get_implied_sample_size("educated guess")
        20.0

        Get the implied sample size for "educated guess" conviction level with an adjustment factor of 0.8:
        >>> get_implied_sample_size("educated guess", adjustment=0.8)
        16.0
    """
    return _get_implied_sample_size(conviction, adjustment=adjustment)


@mcp.tool()
def sample_outcomes(
    beta_params: BetaParameters,
    num_samples: int,
    *,
    random_state: int | None = None,
) -> SampleDraw:
    """Sample outcomes based on a probability distribution represented by a beta distribution.

    Args:
        beta_params (BetaParameters): The parameters of the beta distribution.
        num_samples (int): The number of samples to draw. Must be greater than 0.
        random_state (int | None): Optional random seed for reproducibility. Defaults to None.

    Returns:
        SampleDraw: Randomly drawn samples from probability and outcome distributions.

    Raises:
        ValueError: If num_samples is not greater than 0.
    """
    # Validate num_samples
    if num_samples <= 0:
        raise ValueError("num_samples must be greater than 0.")

    # Draw probability samples from the beta distribution
    probs: list[float] = (
        stats.beta(a=beta_params.alpha, b=beta_params.beta).rvs(size=num_samples, random_state=random_state).tolist()
    )

    # Draw outcomes from the binomial distribution using the sampled probabilities
    outcomes = stats.binom.rvs(n=1, p=probs, random_state=random_state)

    # Ensure outcomes is a list of booleans
    outcomes = [bool(outcomes)] if isinstance(outcomes, int) else outcomes.astype(bool).tolist()

    # Create and return the SampleDraw instance
    return SampleDraw.create(outcomes=outcomes, probabilities=probs)


@mcp.tool()
def update_beta_parameters(
    prior: BetaParameters,
    *,
    successes: int = 0,
    failures: int = 0,
) -> BetaParameters:
    """Update beta distribution parameters with new observed data.

    Args:
        prior (BetaParameters): The prior beta distribution parameters.
        successes (int): The number of observed successes. Must be greater than or equal to 0. Defaults to 0.
        failures (int): The number of observed failures. Must be greater than or equal to 0. Defaults to 0.

    Returns:
        BetaParameters: The updated beta distribution parameters.

    Raises:
        ValueError: If successes or failures are negative.

    Examples:
        Update a prior Beta(1.0, 1.0) with 1 successes:
        >>> prior = BetaParameters(alpha=1.0, beta=1.0)
        >>> update_beta_parameters(prior, successes=1)
        BetaParameters(alpha=2.0, beta=1.0)

        Update a prior Beta(12.0, 8.0) with 7 successes and 3 failures:
        >>> prior = BetaParameters(alpha=12.0, beta=8.0)
        >>> update_beta_parameters(prior, successes=7, failures=3)
        BetaParameters(alpha=19.0, beta=11.0)
    """
    # Validate inputs
    if successes < 0:
        raise ValueError(f"successes must be greater than or equal to 0. Got {successes}.")
    if failures < 0:
        raise ValueError(f"failures must be greater than or equal to 0. Got {failures}.")

    # Update alpha and beta parameters
    updated_alpha = prior.alpha + successes
    updated_beta = prior.beta + failures

    # Return updated beta distribution parameters
    return BetaParameters(alpha=updated_alpha, beta=updated_beta)


# Define prompt templates
@mcp.prompt()
def system_prompt() -> str:
    """System prompt for the Bayesian Beta-Binomial MCP server."""
    return f"""
    You are a helpful assistant that provides Bayesian modeling tools using beta-binomial distributions.

    You can help users answer probabilistic questions that can be modeled as beta-binomial problems. For example,
    - "What is the probability of rain tomorrow?"
    - "How likely is it that my new marketing campaign will succeed?"
    - "What's the chances that I'll get a year-end bonus at work?"

    You're job is to:
    1. Help the user frame their question into a Bayesian modeling problem using beta-binomial distributions. For
         example, if the user asks "How likely is it to rain tomorrow?", your job is to help them frame this as a
         problem of estimating the probability of success (rain) based on prior beliefs and observed data.
    2. Elicit prior beliefs and conviction levels from users.
      a. Communicate possible conviction levels to user: {get_args(ConvictionLevel.__value__)}
      b. Use the `get_beta_prior_from_beliefs` function to infer a beta prior based on user's prior probability
        and conviction level.
    3. Once the user's prior beliefs are established, help them update their beliefs with observed data using the
        `update_beta_parameters` function.
    4. Provide confidence intervals for beta distributions using the `get_beta_confidence_interval` function.
    5. Assist users in drawing samples from their beta-binomial models using the `sample_outcomes` function and
        summarize the results for them.

    If the user asks a question that cannot be addressed with Bayesian modeling using beta-binomial distributions,
    politely inform them that you can only assist with probabilistic questions that can be modeled in this way.

    If you cannot answer the user's question with the available tools, respond with:
    "I'm sorry, but I don't have the tools to answer that question."

    You may use multiple tool calls to answer the user's question.

    You may also ask clarifying questions to better understand the user's needs.
    """


if __name__ == "__main__":
    mcp.run()
