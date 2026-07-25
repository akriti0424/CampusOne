from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user
from app.db.session import get_db
from app.modules.auth.model import User
from app.modules.product.model import Product
from app.modules.product.schema import ProductCreate, ProductRead, ProductStatusUpdate
from app.modules.product.service import create_product, list_products


router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def read_products(db: Session = Depends(get_db)):
    return list_products(db)


@router.post("", response_model=ProductRead)
def add_product(payload: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = create_product(db, current_user.id, payload)
    return {
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "negotiable": product.negotiable,
        "image_url": product.image_url,
        "status": product.status,
        "seller_name": current_user.full_name.split()[0],
        "seller_branch": current_user.branch,
    }


@router.patch("/{product_id}/status", response_model=ProductRead)
def update_status(
    product_id: int,
    payload: ProductStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.status = payload.status
    db.commit()
    db.refresh(product)
    return {
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "negotiable": product.negotiable,
        "image_url": product.image_url,
        "status": product.status,
        "seller_name": current_user.full_name.split()[0],
        "seller_branch": current_user.branch,
    }
