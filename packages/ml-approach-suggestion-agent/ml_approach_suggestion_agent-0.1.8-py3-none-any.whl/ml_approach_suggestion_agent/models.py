from pydantic import BaseModel, Field
from typing import Literal

class MethodologyRecommendation(BaseModel):
    selected_methodology: Literal[  "binary_classification",
                                    "multiclass_classification",
                                    "regression",
                                    "timeseries_regression",
                                    "timeseries_binary_classification",
                                    "recommendation_engine",
                                    "timeseries_recommendation_engine",
                                    "clustering",
                                    "anomaly_detection",
                                    "not_applicable"] = Field(..., description="The most appropriate ML approach for this problem")
    
    justification: str = Field( ..., description="Structured explanation with: business goal, prediction type, temporal dependency analysis, and methodology fit")


