from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


class EnergyType(str, Enum):
    ELECTRICITY = "electricity"
    HEAT = "heat"
    KINETIC = "kinetic"
    POTENTIAL = "potential"


class Measurement(str, Enum):
    TONNES = "tonnes"
    LITERS = "liters"
    KWH = "kwh"
    KG = "kg"
    M3 = "m3"


class Item(BaseModel):
    name: str
    measurement: Measurement
    value: float = 0.0


class EnergySource(BaseModel):
    carbon_intensity_kg_per_kwh: float


class Energy(BaseModel):
    amount_kwh: float
    type: str  # key into energy_sources; keep enum for type safety later if desired


class Finance(BaseModel):
    capex_usd: Optional[float] = 0.0
    opex_usd: Optional[float] = 0.0
    revenue_usd: Optional[float] = 0.0


class Process(BaseModel):
    id: str
    materials_input: Dict[str, float] = Field(default_factory=dict)    # material keys
    materials_output: Dict[str, float] = Field(default_factory=dict)   # material keys
    energy_input: Optional[Energy] = None
    energy_output: Optional[Energy] = None
    emissions_kg: Optional[float] = None
    carbon_locked_kg: Optional[float] = None
    finance: Finance = Finance()

    @field_validator("materials_input", "materials_output")
    @classmethod
    def non_negative_materials(cls, v: Dict[str, float]) -> Dict[str, float]:
        for key, val in v.items():
            if val < 0:
                raise ValueError(f"Quantity for '{key}' cannot be negative")
        return v

    @field_validator("emissions_kg", "carbon_locked_kg", "energy_input", "energy_output")
    @classmethod
    def non_negative_physicals(cls, v):
        if v is None:
            return v
        if isinstance(v, Energy):
            if v.amount_kwh < 0:
                raise ValueError("energy.amount_kwh cannot be negative")
        else:
            if v < 0:
                raise ValueError("value cannot be negative")
        return v


class Transformation(BaseModel):
    id: str
    processes: List[Process]


class Transfer(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    quantities: Dict[str, float]  # material keys


class Scenario(BaseModel):
    name: str
    currency: str
    boundaries: List[str]
    energy_sources: Dict[str, EnergySource]
    materials: Dict[str, Item]
    transformations: List[Transformation]
    transfers: List[Transfer]

    @field_validator("transformations")
    @classmethod
    def transformations_non_empty(cls, v: List[Transformation]) -> List[Transformation]:
        if not v:
            raise ValueError("At least one transformation is required")
        for t in v:
            if not t.processes:
                raise ValueError(f"Transformation '{t.id}' must include at least one process")
        return v

    @model_validator(mode="after")
    def validate_references_and_balances(self):
        materials: Dict[str, Item] = self.materials or {}
        energy_sources: Dict[str, EnergySource] = self.energy_sources or {}
        boundaries = set(self.boundaries or [])
        transformations: List[Transformation] = self.transformations or []
        transfers: List[Transfer] = self.transfers or []

        # Every transformation must be declared in boundaries
        for t in transformations:
            if t.id not in boundaries:
                raise ValueError(f"Transformation '{t.id}' not declared in boundaries")

        # Precompute produced outputs per transformation
        produced: Dict[str, Dict[str, float]] = {}
        for t in transformations:
            produced[t.id] = {}
            for p in t.processes:
                for key in p.materials_input.keys():
                    if key not in materials:
                        raise ValueError(f"Process '{p.id}' in '{t.id}' references unknown input material '{key}'")
                for key, qty in p.materials_output.items():
                    if key not in materials:
                        raise ValueError(f"Process '{p.id}' in '{t.id}' references unknown output material '{key}'")
                    produced[t.id][key] = produced[t.id].get(key, 0.0) + qty
                if p.energy_input and p.energy_input.type not in energy_sources:
                    raise ValueError(f"Process '{p.id}' in '{t.id}' references unknown energy source '{p.energy_input.type}'")
                if p.energy_output and p.energy_output.type not in energy_sources:
                    raise ValueError(f"Process '{p.id}' in '{t.id}' references unknown energy source '{p.energy_output.type}'")

        # Transfers: materials exist, boundaries obeyed, and do not exceed produced quantities
        for tr in transfers:
            if tr.from_ not in boundaries or tr.to not in boundaries:
                raise ValueError(f"Transfer from '{tr.from_}' to '{tr.to}' crosses boundary or references unknown transformation")
            if tr.from_ not in produced:
                raise ValueError(f"Transfer source '{tr.from_}' has no produced outputs")
            for key, qty in tr.quantities.items():
                if key not in materials:
                    raise ValueError(f"Transfer references unknown material key: '{key}'")
                if qty < 0:
                    raise ValueError(f"Transfer quantity for '{key}' cannot be negative")
                available = produced[tr.from_].get(key, 0.0)
                if qty > available:
                    raise ValueError(
                        f"Transfer quantity {qty} for '{key}' from '{tr.from_}' exceeds produced amount {available}")

        return self
