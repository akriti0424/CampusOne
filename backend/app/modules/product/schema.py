from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    title: str = Field(min_length=2, max_length=140)
    description: str = Field(min_length=10, max_length=4000)
    price: float = Field(ge=0)
    category: str = Field(min_length=2, max_length=80)
    negotiable: bool = False
    image_url: str | None = None


class ProductRead(BaseModel):
    id: int
    title: str
    description: str
    price: float
    category: str
    negotiable: bool
    image_url: str | None
    status: str
    seller_name: str
    seller_branch: str

    model_config = {"from_attributes": True}


class ProductStatusUpdate(BaseModel):
    status: str = Field(pattern="^(available|sold)$")
