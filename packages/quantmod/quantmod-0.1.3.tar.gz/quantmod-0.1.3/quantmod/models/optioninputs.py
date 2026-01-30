from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class OptionType(str, Enum):
    """Enum for option types"""
    CALL = "call"
    PUT = "put"

    @classmethod
    def from_string(cls, s: str):
        """Convert string to OptionType"""
        s = s.upper()
        if s in ("CE", "CALL", "C"):
            return cls.CALL
        elif s in ("PE", "PUT", "P"):
            return cls.PUT
        raise ValueError(f"Invalid option type: {s}")
    
class ExerciseStyle(str, Enum):
    ASIAN = "asian"
    BARRIER = "barrier"
    EUROPEAN = "european"
    AMERICAN = "american"
    
    @classmethod
    def from_string(cls, s: str):
        """Convert string to OptionType"""
        s = s.upper()
        if s in ("asian", "Asian", "ASIAN"):
            return cls.ASIAN
        elif s in ("barrier", "Barrier", "BARRIER"):
            return cls.BARRIER
        elif s in ("european", "European", "EUROPEAN"):
            return cls.EUROPEAN
        elif s in ("american", "American", "AMERICAN"):
            return cls.AMERICAN
        raise ValueError(f"Invalid Exercise Style: {s}")

class BarrierType(str, Enum):
    UP_AND_OUT = "up_and_out"
    UP_AND_IN = "up_and_in"
    DOWN_AND_OUT = "down_and_out"
    DOWN_AND_IN = "down_and_in"

    @classmethod
    def from_string(cls, s: str):
        """Convert string to BarrierType"""
        s = s.upper()
        if s in ("up_and_out", "Up_and_out", "UP_AND_OUT"):
            return cls.UP_AND_OUT
        elif s in ("up_and_in", "Up_and_in", "UP_AND_IN"):
            return cls.UP_AND_IN
        elif s in ("down_and_out", "Down_and_out", "DOWN_AND_OUT"):
            return cls.DOWN_AND_OUT
        elif s in ("down_and_in", "Down_and_in", "DOWN_AND_IN"):
            return cls.DOWN_AND_IN
        raise ValueError(f"Invalid Barrier Type: {s}")


class OptionInputs(BaseModel):
    """
    Option inputs parameters

    Parameters
    ----------
    - spot : float
        Current price of the underlying asset
    - strike : float
        Strike price of the option
    - rate : float
        Risk-free interest rate (as a decimal)
    - ttm : float
        Time to maturity in years
    - volatility : float
        Implied volatility of the underlying asset (as a decimal)
    - callprice : float, optional
        Market price of call option (used for implied volatility calculation)
    - putprice : float, optional
        Market price of put option (used for implied volatility calculation)

    Returns
    -------
    OptionInputs
        Option inputs parameters

    Raises
    ------
    ValueError
        If any of the input parameters are invalid
    """

    spot: float = Field(..., gt=0, description="Spot price of the underlying asset")
    strike: float = Field(..., gt=0, description="Strike price of the option")
    rate: float = Field(..., ge=0, le=1, description="Risk-free interest rate")
    ttm: float = Field(..., gt=0, description="Time to maturity in years")
    volatility: float = Field(
        ..., gt=0, description="Volatility of the underlying asset"
    )
    callprice: Optional[float] = Field(
        default=None, ge=0, description="Market price of the call option"
    )
    putprice: Optional[float] = Field(
        default=None, ge=0, description="Market price of the put option"
    )
