from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, model_validator
class AuthIn(BaseModel): email: EmailStr; password: str; display_name: str = ''
class RefreshIn(BaseModel): refresh_token: str
class TokenOut(BaseModel): access_token: str; refresh_token: str; token_type: str='bearer'
class ActivityIn(BaseModel):
    name: str; slug: str; description: str=''; cover_url: str|None=None; start_at: datetime|None=None; end_at: datetime|None=None; registration_start_at: datetime|None=None; registration_end_at: datetime|None=None; total_stock: int=0; max_registrations_per_user: int=1
    @field_validator('total_stock', 'max_registrations_per_user')
    @classmethod
    def non_negative(cls, value: int) -> int:
        if value < 0: raise ValueError('must be non-negative')
        return value
    @model_validator(mode='after')
    def valid_window(self):
        if self.registration_start_at and self.registration_end_at and self.registration_start_at >= self.registration_end_at: raise ValueError('registration window is invalid')
        if self.start_at and self.end_at and self.start_at >= self.end_at: raise ValueError('activity window is invalid')
        return self
class ActivityPatch(BaseModel): name: str|None=None; description: str|None=None; cover_url: str|None=None
class ProfilePatch(BaseModel): display_name: str
class InventoryPatch(BaseModel): quantity: int; reason: str='manual adjustment'
class ActivityOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; name:str; slug:str; description:str; status:str; total_stock:int; available_stock:int; reserved_stock:int; sold_stock:int; max_registrations_per_user:int
