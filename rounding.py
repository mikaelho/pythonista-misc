import decimal, json
from pydantic import BaseModel, conlist
from typing import List
import itertools, math

assert decimal.getcontext().rounding == decimal.ROUND_HALF_EVEN

n = decimal.Decimal('2.5')


incoming = {
    'invoice_lines': [
        {
            'description': 'Holvi T-shirt',     
            'quantity': 2,
            'category': 'Clothes', 
            'unit_price_net': '25.00'
        },
        {
            'description': 'Holvi hoodie',
            'quantity': 1,
            'category': 'Clothes', 
            'unit_price_net': '40.00'
        },
        {
            'description': 'Holvi poster', 
            'quantity': 4,
            'category': 'Posters',
            'unit_price_net': '40.00'
        }
    ],
    'payments': [
        {
            'id': 1,
            'amount': '50.00'
        },
        {
            'id': 2,
            'amount': '200.00'
        }
    ]
}


class InvoiceLine(BaseModel):
    description: str
    quantity: int
    category: str
    unit_price_net: decimal.Decimal
    
class Payment(BaseModel):
    id: int
    amount: decimal.Decimal

class Request(BaseModel):
    invoice_lines: conlist(InvoiceLine, min_items=1)
    payments: conlist(Payment, min_items=1)
    
class Categorisation(BaseModel):
    category: str
    net_amount: decimal.Decimal
    
class Categorisations(BaseModel):
    id: int
    categorisations: List[Categorisation]
    

request = Request(**incoming)

print(request)

rounding_options = [math.floor, math.ceil]

c = itertools.combinations_with_replacement(rounding_options, 5)

for d in c:
    print(d)
