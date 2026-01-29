from demo_app.data import products
from demo_app.exceptions import ResourceNotFoundException


class ProductService:
    def get_all_products(self) -> list[dict]:
        return products

    def get_product_by_id(self, product_id: int) -> dict:
        for product in products:
            if product['id'] == product_id:
                return product
        raise ResourceNotFoundException(
            message=f"No product found with id {product_id}"
        )

    def create_new_product(self, product: dict) -> list[dict]:
        products.append(product)
        return products

    def delete_product_by_id(self, product_id: int) -> list[dict]:
        product = self.get_product_by_id(product_id)
        products.remove(product)
        return products

