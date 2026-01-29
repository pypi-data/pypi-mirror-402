from http import HTTPStatus

from webob import Request

from demo_app import app
from demo_app.data import inventory
from demo_app.exceptions import ResourceNotFoundException
from demo_app.service.product_service import ProductService
from poridhiweb.models.responses import JSONResponse, Response


@app.route('/api/products')
class ProductCreatController:
    def __init__(self):
        self.service = ProductService()

    def get(self, request: Request) -> Response:
        return JSONResponse(self.service.get_all_products())

    # Create
    def post(self, request: Request) -> Response:
        products = self.service.create_new_product(
            request.json
        )
        return JSONResponse(products, status=HTTPStatus.CREATED)


@app.route('/api/products/{id:d}')
class ProductModifyController:
    def __init__(self):
        self.service = ProductService()

    def _get_product_not_found_response(self, product_id: int) -> Response:
        raise ResourceNotFoundException(
            message=f"No product found with id {product_id}"
        )

    def get(self, request: Request, id: int) -> Response:
        product = self.service.get_product_by_id(id)
        return JSONResponse(product)

    def delete(self, request: Request, id: int):
        products = self.service.delete_product_by_id(id)
        return JSONResponse(products)


@app.route('/api/products/{category}', allowed_methods=["GET"])
def get_products_by_cat(request: Request, category: str) -> Response:
    if category not in inventory:
        raise ResourceNotFoundException(
            message=f"No product found with category {category}"
        )
    return JSONResponse(inventory[category])


class ExceptionController:
    def get_value_error(self, request: Request) -> Response:
        raise ValueError("This is a test exception")

    def get_generic_exception(self, request: Request) -> Response:
        raise Exception("This is an unhandled exception")


exception_controller = ExceptionController()
app.add_route('/api/exception/value-error', exception_controller.get_value_error, allowed_methods=["GET"])
app.add_route('/api/exception', exception_controller.get_generic_exception, allowed_methods=["GET"])
