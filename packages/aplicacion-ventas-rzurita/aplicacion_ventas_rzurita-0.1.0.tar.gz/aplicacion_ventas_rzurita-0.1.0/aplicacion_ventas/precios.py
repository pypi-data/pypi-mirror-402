class Precios:
    @staticmethod
    def calcular_precio(precio_base,impuesto,descuento):
        return (precio_base + impuesto) - descuento