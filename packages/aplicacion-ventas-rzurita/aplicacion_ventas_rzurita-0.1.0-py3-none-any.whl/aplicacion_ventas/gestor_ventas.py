from .descuentos import Descuentos
from .impuestos import Impuestos
from .precios import Precios

class GestorVentas:
    def __init__(self,precio,impuesto,descuento):
        self.precio=precio
        self.impuesto=Impuestos(impuesto)
        self.descuento=Descuentos(descuento)
        
    def calcular_precio_final(self):
        impuesto_aplicado=self.impuesto.aplicar_impuestos(self.precio)
        descuento_aplicado=self.descuento.aplicar_descuento(self.precio)
        precio_final= Precios.calcular_precio(self.precio,impuesto_aplicado,descuento_aplicado)
        return round(precio_final,2)
    
    