from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, RootModel


class LoincCodeEnum(str, Enum):
    RADIOLOGY_IMAGING = "radiology_imaging"


class SemanticsEnum(str, Enum):
    SPECIALTIES = "specialties"
    OCCUPATION = "occupation"
    MEDICATION = "medication"
    DIAGNOSIS = "diagnosis"
    PROCEDURE_COMPLICATION = "procedure_complication"
    CONDITION = "condition"
    CONDITION_STATUS = "condition_status"
    OBSERVATION_UNIT = "observation_unit"
    OBSERVATION = "observation"
    CARE_PLAN = "record artifact"
    LAB_CONCLUSION = "lab_conclusion"
    ALLERGY_SYMPTOMS = "allergy_symptoms"
    ALLERGENS = "allergens"
    VACCINE = "vaccine"
    ADVISORY_CATEGORY = "advisory_category"
    ADVISORY_NOTE = "advisory_note"
    PHYSICAL_OBJECT = "physical object"
    PROCEDURE = "procedure"
    QUALIFIER_VALUE = "qualifier value"
    CLINICAL_DRUG = "clinical drug"


class GetCodeDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    semantic_tag: Union[SemanticsEnum, LoincCodeEnum, str] = Field(..., alias="semanticTag")
    search_term: str = Field(..., alias="searchTerm")


class SnomedCodeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    code: str
    text: str
    similarity: Optional[float] = None


class SnomedCodeListResponse(RootModel[List[SnomedCodeResponse]]):
    pass
