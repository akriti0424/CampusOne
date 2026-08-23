from sqlalchemy.orm import Session

from app.modules.auth.service import public_user_name
from app.modules.product.model import Product
from app.modules.product.schema import ProductCreate


def create_product(db: Session, seller_id: int, payload: ProductCreate) -> Product:
    product = Product(
        seller_id=seller_id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        price=payload.price,
        category=payload.category.strip(),
        negotiable=payload.negotiable,
        image_url=payload.image_url,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(db: Session) -> list[dict[str, object]]:
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    return [
        {
            "id": product.id,
            "seller_id": product.seller_id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "category": product.category,
            "negotiable": product.negotiable,
            "image_url": product.image_url,
            "status": product.status,
            "seller_name": public_user_name(product.seller),
            "seller_branch": product.seller.branch,
        }
        for product in products
    ]
